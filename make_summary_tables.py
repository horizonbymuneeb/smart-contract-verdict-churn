"""Print markdown tables from results/results.csv and per_class_flips.csv (pasted into summary.md)."""
import pandas as pd
r=pd.read_csv('results/results.csv')
c1=['model','quant','n','parse_fail_rate','strict_json_fail_rate','inconsistent_rate','acc','precision','recall','f1','specificity','pred_vuln_rate','class_acc_on_vuln','class_acc_all_11way','mean_secs']
print(r[c1].to_markdown(index=False)); print()
q=r[r.binary_flips.notna()]
c2=['model','quant','n_paired','binary_flips','binary_flip_rate','binary_flip_ci95','neg_flips','neg_flips_true_vuln','pos_flips','mcnemar_binary_b_c','mcnemar_binary_p','delta_acc','verdict_flips_11way','verdict_flip_rate_11way','verdict_flip_ci95','mcnemar_class_b_c','mcnemar_class_p','delta_class_acc_11way','raw_output_changed']
print(q[c2].to_markdown(index=False)); print()
p=pd.read_csv('results/per_class_flips.csv')
print(p.to_markdown(index=False))
