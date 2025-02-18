

import test_analyzer
for test_name in ['NL_ron', 'PL_ron', 'NH_ron', 'PH_ron', 'CP_PGOOD', 'Startup_Current', 'IABSP2N', 'IABSN2P', 'IDISCHARGE', 'Vout_Functional']:
    analyze = test_analyzer.TestAnalyzer(excel_file="IVM6201_ATE_TM.xlsx", sheet_name="CP", test_name=test_name)
    analyze.analyze_test()