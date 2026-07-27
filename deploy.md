# 배포 가이드

이 대시보드(`고객은 왜 이탈하는가`)를 GitHub·Streamlit Community Cloud로 배포하는 방법입니다.

## 이 앱의 구조

- 상단 6개 차트(① VOC ~ ⑥ 가입기간·이용량)는 `data/` 폴더의 로컬 CSV 5종만 읽습니다. BigQuery 없이도 바로 동작합니다.
- 맨 아래 **"상담원 관점: 직원만족도와 고객 경험"** 섹션(eNPS, 번아웃×CSAT, 교육이수 비교)은 **BigQuery(`data.data_agents` 등)를 직접 조회**합니다. 이 섹션은 BigQuery 인증 정보(Secrets)가 없으면 **에러가 나고 앱이 멈춥니다** — 로컬 CSV로 자동 대체되는 기능은 없습니다. 따라서 이 섹션까지 정상 동작하려면 아래 4번(Secrets 등록)까지 반드시 완료해야 합니다.

## 1. 사전 준비

- GitHub 계정
- Streamlit Community Cloud 계정 (share.streamlit.io, GitHub 계정으로 로그인)
- BigQuery `project-6fcaf3a6-ee2b-4616-8de.data` 데이터셋(`data_agents`, `data_consultations`, `data_satisfaction`)을 조회할 수 있는 서비스 계정과 JSON 키

## 2. 로컬에서 실행해보기

```
pip install -r requirements.txt
streamlit run app.py
```

로컬에서 BigQuery 섹션까지 확인하려면 `.streamlit/secrets.toml`을 만들어 4번과 같은 내용을 넣어두면 됩니다 (이 파일은 `.gitignore`에 포함해서 커밋하지 않을 것).

## 3. GitHub에 올리기

이 저장소는 이미 GitHub([hyeji5721-ui/customer-churn-dashboard](https://github.com/hyeji5721-ui/customer-churn-dashboard))에 연결되어 있습니다. 브랜치는 **`main`**입니다.

```
git add .
git commit -m "커밋 메시지"
git push origin main
```

## 4. Streamlit Community Cloud 배포·Secrets 등록

1. https://share.streamlit.io 접속 → GitHub 계정으로 로그인
2. 앱 생성 시 Repository: `hyeji5721-ui/customer-churn-dashboard`, Branch: `main`, Main file path: `app.py`
3. 서비스 계정 JSON 키 발급 (GCP 콘솔 → IAM 및 관리자 → 서비스 계정 → 키 → 새 키 만들기 → JSON)
   - 조직 정책(`iam.disableServiceAccountKeyCreation`)으로 키 생성이 막혀있다면, IAM 및 관리자 → 조직 정책에서 해당 제약을 프로젝트 단위로 재정의(시행 안 함)할 수 있는지 먼저 확인
   - 서비스 계정에 `BigQuery 데이터 뷰어`, `BigQuery 작업 사용자` 역할 필요
4. Streamlit Cloud → 앱 → Settings → Secrets에 JSON 키 값을 옮겨 붙여넣기:

```toml
[gcp_service_account]
type = "service_account"
project_id = "project-6fcaf3a6-ee2b-4616-8de"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

5. Save → 앱이 자동 재시작 → "상담원 관점" 섹션까지 정상적으로 뜨는지 확인

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `google.auth.exceptions.TransportError` (GCE 메타데이터 서버 관련) | Streamlit Cloud에는 GCE 메타데이터 서버가 없어 기본 인증(ADC)이 실패함 | `app.py`에서 `bigquery.Client()`에 `service_account.Credentials`를 명시적으로 전달하도록 구현되어 있음 — 4번의 Secrets 등록이 안 되어 있으면 이 에러가 남 |
| `ValueError` / `_NO_DB_TYPES_ERROR` | `to_dataframe()` 호출에 필요한 `db-dtypes` 패키지 누락 | `requirements.txt`에 `db-dtypes` 포함 확인 |
| `ModuleNotFoundError: statsmodels` | 번아웃×CSAT 차트의 `trendline="ols"`가 내부적으로 `statsmodels`를 사용 | `requirements.txt`에 `statsmodels` 포함 확인 |
| "조직 정책으로 키 생성이 차단됨" 에러 (GCP 콘솔에서) | 조직 정책 `disableServiceAccountKeyCreation`이 적용되어 있음 | 프로젝트를 본인이 직접 만들었다면 IAM 및 관리자 → 조직 정책에서 프로젝트 단위로 재정의 가능한 경우가 많음. 안 되면 GCP 조직 관리자에게 예외 요청 필요 |
| Secrets 등록했는데도 BigQuery 에러 | 서비스 계정에 `BigQuery 작업 사용자(Job User)` 역할 누락 | IAM에서 역할 추가 후 앱 Reboot |
