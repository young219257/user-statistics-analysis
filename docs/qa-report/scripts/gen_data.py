"""QA 0단계: 정답을 아는 테스트 데이터 생성 (seed 고정).
산출물: /tmp/qa/out/ 아래 CSV(UTF-8, CP949), XLSX(단일 시트), 결합용 school.csv, truth.json
"""
import json
import numpy as np
import pandas as pd

SEED = 20261109
rng = np.random.default_rng(SEED)
OUT = "/tmp/qa/out"
N_SCHOOL, N = 30, 400

# ---- 위계 구조: 학교 30개, 학교 효과(ICC≈0.15) ----
school_codes = [f"{i:05d}" for i in range(101, 101 + N_SCHOOL)]   # 앞자리 0 보존 대상 ("00101"...)
school_eff = rng.normal(0, 4, N_SCHOOL)
school_of = rng.integers(0, N_SCHOOL, N)
region = np.array(["서울", "경기", "부산", "대구", "광주"])[school_of % 5]
gender = rng.choice(["남", "여"], N)
grade = rng.integers(1, 4, N)                       # 고유값 3개 수치 열
study = np.clip(rng.normal(10, 3, N), 0, None)
income_latent = rng.lognormal(mean=8.0, sigma=0.8, size=N)   # 오른쪽 꼬리
# treatment: 공변량(study, grade)과 연관
logit = -2.0 + 0.15 * study + 0.2 * grade
treat = (rng.random(N) < 1 / (1 + np.exp(-logit))).astype(int)
# 성장곡선: 시점별 점수 (개인 절편·기울기)
a_i = rng.normal(0, 5, N) + school_eff[school_of]
b_i = rng.normal(2.0, 0.8, N)
t = np.arange(4)
scores = np.stack([60 + a_i + b_i * k + 0.4 * study + 3 * treat + rng.normal(0, 3, N) for k in t], axis=1)
satis = np.clip(np.round(3 + 0.08 * (study - 10) + rng.normal(0, 1, N)), 1, 5).astype(int)
passed = (scores[:, 3] + rng.normal(0, 4, N) > 72).astype(int)

df = pd.DataFrame({
    "student_id": [f"S{i:04d}" for i in range(1, N + 1)],
    "school_id": [school_codes[i] for i in school_of],
    "region": region, "gender": gender, "treatment": treat, "grade": grade,
    "score_t1": scores[:, 0].round(2), "score_t2": scores[:, 1].round(2),
    "score_t3": scores[:, 2].round(2), "score_t4": scores[:, 3].round(2),
    "study_hours": study.round(2), "income": income_latent.round(0),
    "satisfaction": satis, "passed": passed,
    "survey_date": pd.date_range("2026-03-02", periods=N, freq="D").strftime("%Y-%m-%d"),
    "const_col": "A",
})
clean = df.copy()   # 문제 주입 전 스냅샷 (정답 계산용)

truth = {"seed": SEED, "n_base": N}

# ---- 이상치: study_hours 극단값 10개 ----
out_idx = rng.choice(N, 10, replace=False)
df.loc[out_idx[:5], "study_hours"] = [38, 41, 45, 36, 50]     # 매우 큼
df.loc[out_idx[5:], "study_hours"] = [24, 25, 26, 27, 24.5]   # 중간 극단 (IQR만 잡히고 Z는 놓칠 수 있음)
truth["outlier_rows_study_hours"] = sorted(int(i) for i in out_idx)

# ---- 결측: study_hours 5% MCAR, income MAR (study 낮을수록 결측↑) ----
mcar = rng.choice(np.setdiff1d(np.arange(N), out_idx), int(N * 0.05), replace=False)
df.loc[mcar, "study_hours"] = np.nan
p_miss = 1 / (1 + np.exp(-(-1.5 - 0.3 * (study - 10))))
mar_mask = rng.random(N) < p_miss * 0.5
df.loc[mar_mask, "income"] = np.nan
# 위장 결측 토큰: 다른 열에 분산 주입
disg_cols = {"satisfaction": [999, -1], "region": ["NA", "-", "null", "", " "]}
disg_rows = rng.choice(N, 12, replace=False)
for j, r in enumerate(disg_rows[:6]):
    df.loc[r, "satisfaction"] = [999, -1][j % 2]
for j, r in enumerate(disg_rows[6:]):
    df.loc[r, "region"] = ["NA", "-", "null", "", " ", "NA"][j]
truth["missing"] = {
    "study_hours_mcar_n": int(len(mcar)), "income_mar_n": int(mar_mask.sum()),
    "disguised_satisfaction_rows": [int(i) for i in disg_rows[:6]],
    "disguised_region_rows": [int(i) for i in disg_rows[6:]],
}

# ---- 형식 문제: 쉼표 숫자 문자열 (income 일부) ----
df["income"] = df["income"].astype(object)
comma_idx = [i for i in range(N) if not pd.isna(df.at[i, "income"])][:40]
for i in comma_idx:
    df.at[i, "income"] = f"{int(df.at[i, 'income']):,}"
truth["comma_income_rows"] = comma_idx

# ---- 중복: 완전 중복 5행 + student_id만 같은 3행 ----
dup_full = df.iloc[[0, 1, 2, 3, 4]].copy()
dup_key = df.iloc[[10, 11, 12]].copy()
dup_key["study_hours"] = 7.77
dup_key["satisfaction"] = 3
df = pd.concat([df, dup_full, dup_key], ignore_index=True)
truth["duplicates"] = {"exact_dup_extra_rows": 5, "key_only_dup_extra_rows": 3, "n_total_rows": len(df)}

# ---- 저장 ----
df.to_csv(f"{OUT}/qa_main_utf8.csv", index=False, encoding="utf-8")
df.to_csv(f"{OUT}/qa_main_cp949.csv", index=False, encoding="cp949")
# 주의: 문제 주입 원본 df 를 그대로 xlsx 로 쓰면 income 열이 숫자+문자 혼합이라 서버가 internal_error 로 실패한다(결함 D-24).
#       단일 시트 정상 반입용 xlsx 는 CSV 를 다시 읽은 값으로 만든다. 실패 재현용 파일은 data/qa_mixed_column_minimal.xlsx 참고.
pd.read_csv(f"{OUT}/qa_main_utf8.csv").to_excel(f"{OUT}/qa_main.xlsx", index=False, sheet_name="main")

# ---- 결합용 school 파일: 키 타입 불일치(숫자), 미매칭 키, 1:N ----
school = pd.DataFrame({
    "school_id": [int(c) for c in school_codes[:27]] + [999, 998],   # 숫자 → 앞자리 0 사라짐, 3개 학교 미매칭, 2개 여분
    "school_type": rng.choice(["일반", "특성화"], 29),
    "budget": rng.integers(100, 900, 29),
})
school = pd.concat([school, school.iloc[[0, 1]].assign(budget=[1, 2])], ignore_index=True)   # 1:N (같은 키 2행)
school.to_csv(f"{OUT}/qa_school.csv", index=False)
truth["merge"] = {
    "left_keys": school_codes, "right_numeric_keys": school["school_id"].tolist(),
    "unmatched_left_codes": school_codes[27:], "one_to_many_keys": [int(school_codes[0]), int(school_codes[1])],
}

# ---- 정답 통계 (주입 전 clean 기준 + 주입 후 기준 모두 기록) ----
def desc(s):
    s = pd.to_numeric(s, errors="coerce")
    q1, q3 = s.quantile(.25), s.quantile(.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    z = (s - s.mean()) / s.std(ddof=1)
    mz = 0.6745 * (s - s.median()) / (s - s.median()).abs().median()
    return {"n": int(s.notna().sum()), "mean": float(s.mean()), "std_ddof1": float(s.std(ddof=1)),
            "median": float(s.median()), "q1": float(q1), "q3": float(q3),
            "iqr_bounds": [float(lo), float(hi)], "iqr_outliers": int(((s < lo) | (s > hi)).sum()),
            "z3_outliers": int((z.abs() > 3).sum()), "modz35_outliers": int((mz.abs() > 3.5).sum()),
            "skew": float(s.skew()), "kurt": float(s.kurt())}

work = df.copy()
for c in ["income", "study_hours", "satisfaction"]:
    work[c] = pd.to_numeric(work[c].astype(str).str.replace(",", ""), errors="coerce")
work.loc[work["satisfaction"].isin([999, -1]), "satisfaction"] = np.nan
truth["desc_after_injection"] = {c: desc(work[c]) for c in ["study_hours", "income", "score_t1", "score_t4", "satisfaction"]}
truth["missing_counts_after_injection"] = {c: int(work[c].isna().sum()) for c in work.columns}
truth["n_unique"] = {c: int(df[c].nunique(dropna=True)) for c in df.columns}
json.dump(truth, open(f"{OUT}/truth.json", "w"), ensure_ascii=False, indent=2)
clean.to_csv(f"{OUT}/qa_clean_reference.csv", index=False)
print("rows", len(df), "files written")
