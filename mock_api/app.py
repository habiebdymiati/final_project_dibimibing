"""
Instance API tiruan (mock) grup Angkasa Biru: tiga HRIS perusahaan dan dua sistem grup (LMS, TMS).
Datanya SINTETIS penuh (dibangkitkan deterministik oleh bangun_data.py; tidak ada data pegawai sungguhan).

Meniru perilaku API asli sehingga konektor pipeline tidak perlu diubah:
  Angkasa Biru             : POST /login (bearer token), paginasi ?page=&limit=, pembungkus {"data": {"data": [...]}},
                             getEmployeeIdentification difilter per ?nik= (fan-out per pegawai).
  Angkasa Biru Retail      : autentikasi header api_key / x-api-key, tanpa paginasi, pembungkus {"data": [...]}.
  Angkasa Biru Destination : token bearer statis, paginasi ?page=&per_page=, pembungkus {"data": [...], "meta": {...}}.
  Angkasa Biru LMS dan TMS : sistem grup lintas perusahaan, masing-masing satu endpoint (/assessments, /aspirations);
                             autentikasi dan pembungkus sama dengan Angkasa Biru Retail.

Konfigurasi lewat environment:
  MOCK_SOURCE   angkasabiru | angkasabiruretail | abdestination | lms | tms
  API_PREFIX    /api/portalhc/v1 (AB) | /api (ABR, LMS, TMS) | /api/v1 (ABD)
  MOCK_USERNAME, MOCK_PASSWORD (AB) / MOCK_API_KEY (ABR, LMS, TMS) / MOCK_API_TOKEN (ABD): kredensial yang diterima;
  bila kosong, kredensial apa pun yang tidak kosong diterima.
"""
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bangun_data import bangun

SUMBER = os.environ.get("MOCK_SOURCE", "angkasabiruretail")
PREFIX = os.environ.get("API_PREFIX", "/api").rstrip("/")

# path endpoint Angkasa Biru -> nama dataset (nama fixture); Angkasa Biru Retail memakai nama path apa adanya
PETA_AB = {
    "getRegion": "regions", "getBranch": "branches", "getDirectorate": "directorates",
    "getGroup": "groups", "getDivision": "divisions", "getPosition": "positions",
    "getEmployeeProfile": "employee_profile", "getEmployeeIdentification": "employee_identification",
    "getEmployeeAddress": "employee_address", "getEmployeeLeaveHistory": "employee_leave_history",
    "getEmployeeEducationHistory": "employee_education_history",
    "getEmployeeAssignmentHistory": "employee_assignment_history",
    "getEmployeeFamilyMember": "employee_family_member", "getEmployeePerformance": "employee_performance",
    "getEmployeeLearning": "employee_learning", "getEmployeePositionHistory": "employee_position_history",
    "getUnit": "units", "getPositionMaster": "position_master", "getPositionVariant": "position_variants",
    "getCompany": "companies", "getCompanyAddress": "company_addresses",
    "getCompanyDocument": "company_documents", "getCompanyType": "company_types",
    "getBand": "bands", "getPositionType": "position_types",
    "getPositionCompetencyRequirement": "position_competency_requirements",
    "getJobFamily": "job_families", "getJobFunction": "job_functions",
    # endpoint yang tidak ada di API asli: dilengkapi instance tiruan
    "getCompetencyAssessment": "competency_assessment",
}

# path endpoint Angkasa Biru Destination (HRIS ABD) -> nama dataset
PETA_ABD = {
    "organization/company-types": "company_types", "organization/companies": "companies",
    "organization/company-addresses": "company_addresses", "organization/company-documents": "company_documents",
    "organization/org-unit-types": "org_unit_types", "organization/org-units": "org_units",
    "organization/org-unit-documents": "org_unit_documents", "organization/job-families": "job_families",
    "organization/job-functions": "job_functions", "organization/position-types": "position_types",
    "organization/position-masters": "position_masters", "organization/position-variants": "position_variants",
    "organization/bands": "bands", "organization/position-documents": "position_documents",
    "organization/position-competency-requirements": "position_competency_requirements",
    "organization/employee-position-histories": "employee_position_histories",
    "organization/employee-secondary-assignments": "employee_secondary_assignments",
    "employee/profiles": "employee_profiles", "employee/identifications": "employee_identifications",
    "employee/addresses": "employee_addresses", "employee/performance-histories": "employee_performance_histories",
    "employee/leave-histories": "employee_leave_histories",
    "employee/education-histories": "employee_education_histories",
    "employee/assignment-histories": "employee_assignment_histories",
    "employee/family-members": "employee_family_members",
    "transaction/contracts": "employee_contracts", "transaction/performance-histories": "performance_histories",
    "transaction/learning-histories": "learning_histories",
    # tidak ada di koleksi Postman; dilengkapi instance tiruan (katalog BRD 4.5)
    "transaction/competency-assessments": "competency_assessments",
}

# path endpoint LMS (sistem grup, katalog BRD 4.4) -> nama dataset
PETA_LMS = {"assessments": "learning_agility_assessments"}

# path endpoint TMS (sistem talenta grup, katalog BRD 5.1) -> nama dataset
PETA_TMS = {"aspirations": "career_aspirations"}

app = FastAPI(title=f"Mock API {SUMBER}")
DATA: dict = {}
TOKEN_AKTIF: set = set()


@app.on_event("startup")
def _siapkan():
    DATA.update(bangun(SUMBER))


@app.get("/health")
def health():
    return {"status": "ok", "source": SUMBER, "datasets": len(DATA)}


@app.post(f"{PREFIX}/login")
def login(body: dict):
    harap_user = os.environ.get("MOCK_USERNAME", "")
    harap_pass = os.environ.get("MOCK_PASSWORD", "")
    user, pwd = body.get("username", ""), body.get("password", "")
    cocok = (user == harap_user and pwd == harap_pass) if (harap_user or harap_pass) else bool(user and pwd)
    if not cocok:
        return JSONResponse({"message": "Unauthorized"}, status_code=401)
    token = secrets.token_hex(16)
    TOKEN_AKTIF.add(token)
    return {"token": token}


def _cek_auth(request: Request):
    if SUMBER == "abdestination":
        # token bearer statis (gaya HRIS ABD), tanpa endpoint login
        harap = os.environ.get("MOCK_API_TOKEN", "")
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer ") or (harap and auth[7:] != harap) or auth[7:] == "":
            return JSONResponse({"message": "Unauthorized"}, status_code=401)
        return None
    if SUMBER == "angkasabiru":
        auth = request.headers.get("authorization", "")
        if not (auth.startswith("Bearer ") and auth[7:] in TOKEN_AKTIF):
            return JSONResponse({"message": "Unauthorized"}, status_code=401)
        return None
    kunci = request.headers.get("api_key") or request.headers.get("x-api-key") or ""
    harap = os.environ.get("MOCK_API_KEY", "")
    if (harap and kunci != harap) or not kunci:
        return JSONResponse({"message": "Unauthorized"}, status_code=401)
    return None


@app.get(f"{PREFIX}/{{jalur:path}}")
def ambil(jalur: str, request: Request):
    salah = _cek_auth(request)
    if salah is not None:
        return salah
    nama = PETA_AB.get(jalur) if SUMBER == "angkasabiru" else \
        PETA_ABD.get(jalur) if SUMBER == "abdestination" else \
        PETA_LMS.get(jalur) if SUMBER == "lms" else \
        PETA_TMS.get(jalur) if SUMBER == "tms" else jalur
    if nama is None or nama not in DATA:
        return JSONResponse({"message": "Not Found"}, status_code=404)
    baris = DATA[nama]

    nik = request.query_params.get("nik")
    if nik is not None:                                 # fan-out per pegawai (getEmployeeIdentification)
        baris = [b for b in baris if str(b.get("id_employee")) == nik]

    if SUMBER == "abdestination":                         # paginasi ?page=&per_page= (maksimum 500)
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            per_page = min(500, max(1, int(request.query_params.get("per_page", 100))))
        except ValueError:
            return JSONResponse({"message": "Bad Request"}, status_code=400)
        potong = baris[(page - 1) * per_page: page * per_page]
        return {"data": potong, "meta": {"page": page, "per_page": per_page, "total": len(baris)}}
    if SUMBER == "angkasabiru":                         # paginasi ?page=&limit= seperti API asli
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            limit = max(1, int(request.query_params.get("limit", 2000)))
        except ValueError:
            return JSONResponse({"message": "Bad Request"}, status_code=400)
        potong = baris[(page - 1) * limit: page * limit]
        return {"data": {"data": potong, "page": page, "limit": limit, "total": len(baris)}}
    return {"data": baris}
