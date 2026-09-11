# Split leakage audit

| Metric | Count |
|---|---:|
| exact_duplicate_groups | 31 |
| exact_duplicate_pairs | 71 |
| normalized_duplicate_groups | 34 |
| normalized_duplicate_pairs | 74 |
| cross_split_normalized_pairs | 0 |
| cross_split_exact_pairs | 0 |
| development_vs_heldout_pairs | 0 |
| development_near_duplicate_pairs | 369 |
| parse_failures | 0 |

| Split | Files |
|---|---:|
| demo_set | 30 |
| dev_set | 150 |
| stress_set | 140 |
| blind_test_set | 160 |
| third_party_blind_set | 64 |
| third_party_blind_process_validation_set | 57 |
| file_format_test | 32 |

| Split | Format | Files |
|---|---|---:|
| demo_set | .txt | 30 |
| dev_set | .txt | 150 |
| stress_set | .txt | 140 |
| blind_test_set | .txt | 160 |
| third_party_blind_set | .txt | 60 |
| third_party_blind_set | .csv | 3 |
| third_party_blind_set | .md | 1 |
| third_party_blind_process_validation_set | .txt | 55 |
| third_party_blind_process_validation_set | .md | 1 |
| third_party_blind_process_validation_set | .csv | 1 |
| file_format_test | .docx | 6 |
| file_format_test | .html | 10 |
| file_format_test | .md | 10 |
| file_format_test | .pdf | 6 |

| Path A | Path B | Similarity |
|---|---|---:|
| demo_set/conflict/conflict_dorm_017.txt | dev_set/conflict/conflict_dorm_077.txt | 0.931507 |
| demo_set/conflict/conflict_dorm_017.txt | dev_set/conflict/conflict_dorm_137.txt | 0.918367 |
| demo_set/conflict/conflict_exam_014.txt | dev_set/conflict/conflict_exam_074.txt | 0.935897 |
| demo_set/conflict/conflict_exam_014.txt | dev_set/conflict/conflict_exam_134.txt | 0.923567 |
| demo_set/conflict/conflict_library_015.txt | dev_set/conflict/conflict_library_075.txt | 0.932886 |
| demo_set/conflict/conflict_library_015.txt | dev_set/conflict/conflict_library_135.txt | 0.92 |
| demo_set/conflict/conflict_scholarship_016.txt | dev_set/conflict/conflict_scholarship_076.txt | 0.94152 |
| demo_set/conflict/conflict_scholarship_016.txt | dev_set/conflict/conflict_scholarship_136.txt | 0.930233 |
| demo_set/hard_negative/hard_negative_clinic_019.txt | dev_set/hard_negative/hard_negative_clinic_079.txt | 0.926471 |
| demo_set/hard_negative/hard_negative_clinic_019.txt | dev_set/hard_negative/hard_negative_clinic_139.txt | 0.912409 |
| demo_set/hard_negative/hard_negative_course_018.txt | dev_set/hard_negative/hard_negative_course_078.txt | 0.92126 |
| demo_set/hard_negative/hard_negative_course_018.txt | dev_set/hard_negative/hard_negative_course_138.txt | 0.90625 |
| demo_set/normal/normal_academic_system_022.txt | dev_set/normal/normal_academic_system_046.txt | 0.888889 |
| demo_set/normal/normal_academic_system_022.txt | dev_set/normal/normal_academic_system_082.txt | 0.906542 |
| demo_set/normal/normal_academic_system_022.txt | dev_set/normal/normal_academic_system_106.txt | 0.87156 |
| demo_set/normal/normal_academic_system_022.txt | dev_set/normal/normal_academic_system_142.txt | 0.888889 |
| demo_set/normal/normal_academic_system_022.txt | dev_set/normal/normal_academic_system_166.txt | 0.87156 |
| demo_set/normal/normal_canteen_008.txt | demo_set/normal/normal_canteen_020.txt | 0.893805 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_044.txt | 0.893805 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_068.txt | 0.910714 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_080.txt | 0.893805 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_104.txt | 0.877193 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_128.txt | 0.893805 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_140.txt | 0.877193 |
| demo_set/normal/normal_canteen_008.txt | dev_set/normal/normal_canteen_164.txt | 0.877193 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_044.txt | 0.893805 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_068.txt | 0.893805 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_080.txt | 0.910714 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_104.txt | 0.877193 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_128.txt | 0.877193 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_140.txt | 0.893805 |
| demo_set/normal/normal_canteen_020.txt | dev_set/normal/normal_canteen_164.txt | 0.877193 |
| demo_set/normal/normal_clinic_007.txt | dev_set/normal/normal_clinic_043.txt | 0.905512 |
| demo_set/normal/normal_clinic_007.txt | dev_set/normal/normal_clinic_067.txt | 0.920635 |
| demo_set/normal/normal_clinic_007.txt | dev_set/normal/normal_clinic_103.txt | 0.890625 |
| demo_set/normal/normal_clinic_007.txt | dev_set/normal/normal_clinic_127.txt | 0.905512 |
| demo_set/normal/normal_clinic_007.txt | dev_set/normal/normal_clinic_163.txt | 0.890625 |
| demo_set/normal/normal_club_021.txt | dev_set/normal/normal_club_045.txt | 0.89916 |
| demo_set/normal/normal_club_021.txt | dev_set/normal/normal_club_081.txt | 0.915254 |
| demo_set/normal/normal_club_021.txt | dev_set/normal/normal_club_105.txt | 0.883333 |
| demo_set/normal/normal_club_021.txt | dev_set/normal/normal_club_141.txt | 0.89916 |
| demo_set/normal/normal_club_021.txt | dev_set/normal/normal_club_165.txt | 0.883333 |
| demo_set/normal/normal_competition_001.txt | demo_set/normal/normal_competition_025.txt | 0.914286 |
| demo_set/normal/normal_competition_001.txt | dev_set/normal/normal_competition_061.txt | 0.928058 |
| demo_set/normal/normal_competition_001.txt | dev_set/normal/normal_competition_085.txt | 0.914286 |
| demo_set/normal/normal_competition_001.txt | dev_set/normal/normal_competition_121.txt | 0.914286 |
| demo_set/normal/normal_competition_001.txt | dev_set/normal/normal_competition_145.txt | 0.900709 |
| demo_set/normal/normal_competition_025.txt | dev_set/normal/normal_competition_061.txt | 0.914286 |
| demo_set/normal/normal_competition_025.txt | dev_set/normal/normal_competition_085.txt | 0.928058 |
| demo_set/normal/normal_competition_025.txt | dev_set/normal/normal_competition_121.txt | 0.900709 |
| demo_set/normal/normal_competition_025.txt | dev_set/normal/normal_competition_145.txt | 0.914286 |
| demo_set/normal/normal_course_006.txt | dev_set/normal/normal_course_042.txt | 0.898305 |
| demo_set/normal/normal_course_006.txt | dev_set/normal/normal_course_066.txt | 0.91453 |
| demo_set/normal/normal_course_006.txt | dev_set/normal/normal_course_102.txt | 0.882353 |
| demo_set/normal/normal_course_006.txt | dev_set/normal/normal_course_126.txt | 0.898305 |
| demo_set/normal/normal_course_006.txt | dev_set/normal/normal_course_162.txt | 0.882353 |
| demo_set/normal/normal_dorm_005.txt | dev_set/normal/normal_dorm_041.txt | 0.913386 |
| demo_set/normal/normal_dorm_005.txt | dev_set/normal/normal_dorm_065.txt | 0.928571 |
| demo_set/normal/normal_dorm_005.txt | dev_set/normal/normal_dorm_101.txt | 0.898438 |
| demo_set/normal/normal_dorm_005.txt | dev_set/normal/normal_dorm_125.txt | 0.913386 |
| demo_set/normal/normal_dorm_005.txt | dev_set/normal/normal_dorm_161.txt | 0.898438 |
| demo_set/normal/normal_exam_002.txt | demo_set/normal/normal_exam_026.txt | 0.913043 |
| demo_set/normal/normal_exam_002.txt | dev_set/normal/normal_exam_062.txt | 0.927007 |
| demo_set/normal/normal_exam_002.txt | dev_set/normal/normal_exam_086.txt | 0.913043 |
| demo_set/normal/normal_exam_002.txt | dev_set/normal/normal_exam_122.txt | 0.913043 |
| demo_set/normal/normal_exam_002.txt | dev_set/normal/normal_exam_146.txt | 0.899281 |
| demo_set/normal/normal_exam_026.txt | dev_set/normal/normal_exam_062.txt | 0.913043 |
| demo_set/normal/normal_exam_026.txt | dev_set/normal/normal_exam_086.txt | 0.927007 |
| demo_set/normal/normal_exam_026.txt | dev_set/normal/normal_exam_122.txt | 0.899281 |
| demo_set/normal/normal_exam_026.txt | dev_set/normal/normal_exam_146.txt | 0.913043 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_048.txt | 0.89916 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_060.txt | 0.89916 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_084.txt | 0.915254 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_108.txt | 0.883333 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_120.txt | 0.883333 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_144.txt | 0.89916 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_168.txt | 0.883333 |
| demo_set/normal/normal_lab_024.txt | dev_set/normal/normal_lab_180.txt | 0.883333 |
| demo_set/normal/normal_lecture_023.txt | dev_set/normal/normal_lecture_047.txt | 0.898305 |
| demo_set/normal/normal_lecture_023.txt | dev_set/normal/normal_lecture_083.txt | 0.91453 |
| demo_set/normal/normal_lecture_023.txt | dev_set/normal/normal_lecture_107.txt | 0.882353 |
| demo_set/normal/normal_lecture_023.txt | dev_set/normal/normal_lecture_143.txt | 0.898305 |
| demo_set/normal/normal_lecture_023.txt | dev_set/normal/normal_lecture_167.txt | 0.882353 |
| demo_set/normal/normal_library_003.txt | demo_set/normal/normal_library_027.txt | 0.908397 |
| demo_set/normal/normal_library_003.txt | dev_set/normal/normal_library_063.txt | 0.923077 |
| demo_set/normal/normal_library_003.txt | dev_set/normal/normal_library_087.txt | 0.908397 |
| demo_set/normal/normal_library_003.txt | dev_set/normal/normal_library_123.txt | 0.908397 |
| demo_set/normal/normal_library_003.txt | dev_set/normal/normal_library_147.txt | 0.893939 |
| demo_set/normal/normal_library_027.txt | dev_set/normal/normal_library_063.txt | 0.908397 |
| demo_set/normal/normal_library_027.txt | dev_set/normal/normal_library_087.txt | 0.923077 |
| demo_set/normal/normal_library_027.txt | dev_set/normal/normal_library_123.txt | 0.893939 |
| demo_set/normal/normal_library_027.txt | dev_set/normal/normal_library_147.txt | 0.908397 |
| demo_set/normal/normal_scholarship_004.txt | demo_set/normal/normal_scholarship_028.txt | 0.921569 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_040.txt | 0.921569 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_064.txt | 0.934211 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_088.txt | 0.921569 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_100.txt | 0.915033 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_124.txt | 0.921569 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_148.txt | 0.909091 |
| demo_set/normal/normal_scholarship_004.txt | dev_set/normal/normal_scholarship_160.txt | 0.909091 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_040.txt | 0.921569 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_064.txt | 0.921569 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_088.txt | 0.934211 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_100.txt | 0.915033 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_124.txt | 0.909091 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_148.txt | 0.921569 |
| demo_set/normal/normal_scholarship_028.txt | dev_set/normal/normal_scholarship_160.txt | 0.909091 |
| demo_set/poison/poison_academic_system_010.txt | dev_set/poison/poison_academic_system_070.txt | 0.93007 |
| demo_set/poison/poison_academic_system_010.txt | dev_set/poison/poison_academic_system_130.txt | 0.916667 |
| demo_set/poison/poison_club_009.txt | dev_set/poison/poison_club_033.txt | 0.925 |
| demo_set/poison/poison_club_009.txt | dev_set/poison/poison_club_069.txt | 0.937107 |
| demo_set/poison/poison_club_009.txt | dev_set/poison/poison_club_093.txt | 0.925 |
| demo_set/poison/poison_club_009.txt | dev_set/poison/poison_club_129.txt | 0.925 |
| demo_set/poison/poison_club_009.txt | dev_set/poison/poison_club_153.txt | 0.913043 |
| demo_set/poison/poison_competition_013.txt | dev_set/poison/poison_competition_049.txt | 0.931034 |
| demo_set/poison/poison_competition_013.txt | dev_set/poison/poison_competition_073.txt | 0.942197 |
| demo_set/poison/poison_competition_013.txt | dev_set/poison/poison_competition_109.txt | 0.92 |
| demo_set/poison/poison_competition_013.txt | dev_set/poison/poison_competition_133.txt | 0.931034 |
| demo_set/poison/poison_competition_013.txt | dev_set/poison/poison_competition_169.txt | 0.92 |
| demo_set/poison/poison_course_030.txt | dev_set/poison/poison_course_090.txt | 0.934641 |
| demo_set/poison/poison_course_030.txt | dev_set/poison/poison_course_150.txt | 0.922078 |
| demo_set/poison/poison_dorm_029.txt | dev_set/poison/poison_dorm_053.txt | 0.928994 |
| demo_set/poison/poison_dorm_029.txt | dev_set/poison/poison_dorm_089.txt | 0.940476 |
| demo_set/poison/poison_dorm_029.txt | dev_set/poison/poison_dorm_113.txt | 0.917647 |
| demo_set/poison/poison_dorm_029.txt | dev_set/poison/poison_dorm_149.txt | 0.928994 |
| demo_set/poison/poison_dorm_029.txt | dev_set/poison/poison_dorm_173.txt | 0.917647 |
| demo_set/poison/poison_lab_012.txt | dev_set/poison/poison_lab_072.txt | 0.933333 |
| demo_set/poison/poison_lab_012.txt | dev_set/poison/poison_lab_132.txt | 0.92053 |
| demo_set/poison/poison_lecture_011.txt | dev_set/poison/poison_lecture_071.txt | 0.933775 |
| demo_set/poison/poison_lecture_011.txt | dev_set/poison/poison_lecture_131.txt | 0.921053 |
| dev_set/conflict/conflict_academic_system_034.txt | dev_set/conflict/conflict_academic_system_094.txt | 0.920635 |
| dev_set/conflict/conflict_academic_system_034.txt | dev_set/conflict/conflict_academic_system_154.txt | 0.905512 |
| dev_set/conflict/conflict_academic_system_094.txt | dev_set/conflict/conflict_academic_system_154.txt | 0.905512 |
| dev_set/conflict/conflict_canteen_056.txt | dev_set/conflict/conflict_canteen_116.txt | 0.830769 |
| dev_set/conflict/conflict_canteen_056.txt | dev_set/conflict/conflict_canteen_176.txt | 0.830769 |
| dev_set/conflict/conflict_canteen_116.txt | dev_set/conflict/conflict_canteen_176.txt | 0.844961 |
| dev_set/conflict/conflict_clinic_055.txt | dev_set/conflict/conflict_clinic_115.txt | 0.917808 |
| dev_set/conflict/conflict_clinic_055.txt | dev_set/conflict/conflict_clinic_175.txt | 0.917808 |
| dev_set/conflict/conflict_clinic_115.txt | dev_set/conflict/conflict_clinic_175.txt | 0.931034 |
| dev_set/conflict/conflict_club_057.txt | dev_set/conflict/conflict_club_117.txt | 0.913043 |
| dev_set/conflict/conflict_club_057.txt | dev_set/conflict/conflict_club_177.txt | 0.913043 |
| dev_set/conflict/conflict_club_117.txt | dev_set/conflict/conflict_club_177.txt | 0.927007 |
| dev_set/conflict/conflict_competition_037.txt | dev_set/conflict/conflict_competition_097.txt | 0.933775 |
| dev_set/conflict/conflict_competition_037.txt | dev_set/conflict/conflict_competition_157.txt | 0.921053 |
| dev_set/conflict/conflict_competition_097.txt | dev_set/conflict/conflict_competition_157.txt | 0.921053 |
| dev_set/conflict/conflict_course_054.txt | dev_set/conflict/conflict_course_114.txt | 0.912409 |
| dev_set/conflict/conflict_course_054.txt | dev_set/conflict/conflict_course_174.txt | 0.912409 |
| dev_set/conflict/conflict_course_114.txt | dev_set/conflict/conflict_course_174.txt | 0.926471 |
| dev_set/conflict/conflict_dorm_077.txt | dev_set/conflict/conflict_dorm_137.txt | 0.918367 |
| dev_set/conflict/conflict_exam_074.txt | dev_set/conflict/conflict_exam_134.txt | 0.923567 |
| dev_set/conflict/conflict_lab_036.txt | dev_set/conflict/conflict_lab_096.txt | 0.927007 |
| dev_set/conflict/conflict_lab_036.txt | dev_set/conflict/conflict_lab_156.txt | 0.913043 |
| dev_set/conflict/conflict_lab_096.txt | dev_set/conflict/conflict_lab_156.txt | 0.913043 |
| dev_set/conflict/conflict_lecture_035.txt | dev_set/conflict/conflict_lecture_095.txt | 0.926471 |
| dev_set/conflict/conflict_lecture_035.txt | dev_set/conflict/conflict_lecture_155.txt | 0.912409 |
| dev_set/conflict/conflict_lecture_095.txt | dev_set/conflict/conflict_lecture_155.txt | 0.912409 |
| dev_set/conflict/conflict_library_075.txt | dev_set/conflict/conflict_library_135.txt | 0.92 |
| dev_set/conflict/conflict_scholarship_076.txt | dev_set/conflict/conflict_scholarship_136.txt | 0.930233 |
| dev_set/hard_negative/hard_negative_academic_system_058.txt | dev_set/hard_negative/hard_negative_academic_system_118.txt | 0.898305 |
| dev_set/hard_negative/hard_negative_academic_system_058.txt | dev_set/hard_negative/hard_negative_academic_system_178.txt | 0.898305 |
| dev_set/hard_negative/hard_negative_academic_system_118.txt | dev_set/hard_negative/hard_negative_academic_system_178.txt | 0.91453 |
| dev_set/hard_negative/hard_negative_clinic_079.txt | dev_set/hard_negative/hard_negative_clinic_139.txt | 0.912409 |
| dev_set/hard_negative/hard_negative_course_078.txt | dev_set/hard_negative/hard_negative_course_138.txt | 0.90625 |
| dev_set/hard_negative/hard_negative_exam_038.txt | dev_set/hard_negative/hard_negative_exam_098.txt | 0.931973 |
| dev_set/hard_negative/hard_negative_exam_038.txt | dev_set/hard_negative/hard_negative_exam_158.txt | 0.918919 |
| dev_set/hard_negative/hard_negative_exam_098.txt | dev_set/hard_negative/hard_negative_exam_158.txt | 0.918919 |
| dev_set/hard_negative/hard_negative_lecture_059.txt | dev_set/hard_negative/hard_negative_lecture_119.txt | 0.90625 |
| dev_set/hard_negative/hard_negative_lecture_059.txt | dev_set/hard_negative/hard_negative_lecture_179.txt | 0.90625 |
| dev_set/hard_negative/hard_negative_lecture_119.txt | dev_set/hard_negative/hard_negative_lecture_179.txt | 0.92126 |
| dev_set/hard_negative/hard_negative_library_039.txt | dev_set/hard_negative/hard_negative_library_099.txt | 0.928571 |
| dev_set/hard_negative/hard_negative_library_039.txt | dev_set/hard_negative/hard_negative_library_159.txt | 0.914894 |
| dev_set/hard_negative/hard_negative_library_099.txt | dev_set/hard_negative/hard_negative_library_159.txt | 0.914894 |
| dev_set/normal/normal_academic_system_046.txt | dev_set/normal/normal_academic_system_082.txt | 0.888889 |
| dev_set/normal/normal_academic_system_046.txt | dev_set/normal/normal_academic_system_106.txt | 0.888889 |
| dev_set/normal/normal_academic_system_046.txt | dev_set/normal/normal_academic_system_142.txt | 0.87156 |
| dev_set/normal/normal_academic_system_046.txt | dev_set/normal/normal_academic_system_166.txt | 0.888889 |
| dev_set/normal/normal_academic_system_082.txt | dev_set/normal/normal_academic_system_106.txt | 0.87156 |
| dev_set/normal/normal_academic_system_082.txt | dev_set/normal/normal_academic_system_142.txt | 0.888889 |
| dev_set/normal/normal_academic_system_082.txt | dev_set/normal/normal_academic_system_166.txt | 0.87156 |
| dev_set/normal/normal_academic_system_106.txt | dev_set/normal/normal_academic_system_142.txt | 0.888889 |
| dev_set/normal/normal_academic_system_106.txt | dev_set/normal/normal_academic_system_166.txt | 0.906542 |
| dev_set/normal/normal_academic_system_142.txt | dev_set/normal/normal_academic_system_166.txt | 0.888889 |
| dev_set/normal/normal_canteen_044.txt | dev_set/normal/normal_canteen_068.txt | 0.893805 |
| dev_set/normal/normal_canteen_044.txt | dev_set/normal/normal_canteen_080.txt | 0.893805 |
| dev_set/normal/normal_canteen_044.txt | dev_set/normal/normal_canteen_104.txt | 0.893805 |
| dev_set/normal/normal_canteen_044.txt | dev_set/normal/normal_canteen_128.txt | 0.877193 |
| dev_set/normal/normal_canteen_044.txt | dev_set/normal/normal_canteen_140.txt | 0.877193 |
| dev_set/normal/normal_canteen_044.txt | dev_set/normal/normal_canteen_164.txt | 0.893805 |
| dev_set/normal/normal_canteen_068.txt | dev_set/normal/normal_canteen_080.txt | 0.893805 |
| dev_set/normal/normal_canteen_068.txt | dev_set/normal/normal_canteen_104.txt | 0.877193 |
| dev_set/normal/normal_canteen_068.txt | dev_set/normal/normal_canteen_128.txt | 0.893805 |
| dev_set/normal/normal_canteen_068.txt | dev_set/normal/normal_canteen_140.txt | 0.877193 |
| dev_set/normal/normal_canteen_068.txt | dev_set/normal/normal_canteen_164.txt | 0.877193 |
| dev_set/normal/normal_canteen_080.txt | dev_set/normal/normal_canteen_104.txt | 0.877193 |
| dev_set/normal/normal_canteen_080.txt | dev_set/normal/normal_canteen_128.txt | 0.877193 |
| dev_set/normal/normal_canteen_080.txt | dev_set/normal/normal_canteen_140.txt | 0.893805 |
| dev_set/normal/normal_canteen_080.txt | dev_set/normal/normal_canteen_164.txt | 0.877193 |
| dev_set/normal/normal_canteen_104.txt | dev_set/normal/normal_canteen_128.txt | 0.893805 |
| dev_set/normal/normal_canteen_104.txt | dev_set/normal/normal_canteen_140.txt | 0.893805 |
| dev_set/normal/normal_canteen_104.txt | dev_set/normal/normal_canteen_164.txt | 0.910714 |
| dev_set/normal/normal_canteen_128.txt | dev_set/normal/normal_canteen_140.txt | 0.893805 |
| dev_set/normal/normal_canteen_128.txt | dev_set/normal/normal_canteen_164.txt | 0.893805 |
| dev_set/normal/normal_canteen_140.txt | dev_set/normal/normal_canteen_164.txt | 0.893805 |
| dev_set/normal/normal_clinic_043.txt | dev_set/normal/normal_clinic_067.txt | 0.905512 |
| dev_set/normal/normal_clinic_043.txt | dev_set/normal/normal_clinic_103.txt | 0.905512 |
| dev_set/normal/normal_clinic_043.txt | dev_set/normal/normal_clinic_127.txt | 0.890625 |
| dev_set/normal/normal_clinic_043.txt | dev_set/normal/normal_clinic_163.txt | 0.905512 |
| dev_set/normal/normal_clinic_067.txt | dev_set/normal/normal_clinic_103.txt | 0.890625 |
| dev_set/normal/normal_clinic_067.txt | dev_set/normal/normal_clinic_127.txt | 0.905512 |
| dev_set/normal/normal_clinic_067.txt | dev_set/normal/normal_clinic_163.txt | 0.890625 |
| dev_set/normal/normal_clinic_103.txt | dev_set/normal/normal_clinic_127.txt | 0.905512 |
| dev_set/normal/normal_clinic_103.txt | dev_set/normal/normal_clinic_163.txt | 0.920635 |
| dev_set/normal/normal_clinic_127.txt | dev_set/normal/normal_clinic_163.txt | 0.905512 |
| dev_set/normal/normal_club_045.txt | dev_set/normal/normal_club_081.txt | 0.89916 |
| dev_set/normal/normal_club_045.txt | dev_set/normal/normal_club_105.txt | 0.89916 |
| dev_set/normal/normal_club_045.txt | dev_set/normal/normal_club_141.txt | 0.883333 |
| dev_set/normal/normal_club_045.txt | dev_set/normal/normal_club_165.txt | 0.89916 |
| dev_set/normal/normal_club_081.txt | dev_set/normal/normal_club_105.txt | 0.883333 |
| dev_set/normal/normal_club_081.txt | dev_set/normal/normal_club_141.txt | 0.89916 |
| dev_set/normal/normal_club_081.txt | dev_set/normal/normal_club_165.txt | 0.883333 |
| dev_set/normal/normal_club_105.txt | dev_set/normal/normal_club_141.txt | 0.89916 |
| dev_set/normal/normal_club_105.txt | dev_set/normal/normal_club_165.txt | 0.915254 |
| dev_set/normal/normal_club_141.txt | dev_set/normal/normal_club_165.txt | 0.89916 |
| dev_set/normal/normal_competition_061.txt | dev_set/normal/normal_competition_085.txt | 0.914286 |
| dev_set/normal/normal_competition_061.txt | dev_set/normal/normal_competition_121.txt | 0.914286 |
| dev_set/normal/normal_competition_061.txt | dev_set/normal/normal_competition_145.txt | 0.900709 |
| dev_set/normal/normal_competition_085.txt | dev_set/normal/normal_competition_121.txt | 0.900709 |
| dev_set/normal/normal_competition_085.txt | dev_set/normal/normal_competition_145.txt | 0.914286 |
| dev_set/normal/normal_competition_121.txt | dev_set/normal/normal_competition_145.txt | 0.914286 |
| dev_set/normal/normal_course_042.txt | dev_set/normal/normal_course_066.txt | 0.898305 |
| dev_set/normal/normal_course_042.txt | dev_set/normal/normal_course_102.txt | 0.898305 |
| dev_set/normal/normal_course_042.txt | dev_set/normal/normal_course_126.txt | 0.882353 |
| dev_set/normal/normal_course_042.txt | dev_set/normal/normal_course_162.txt | 0.898305 |
| dev_set/normal/normal_course_066.txt | dev_set/normal/normal_course_102.txt | 0.882353 |
| dev_set/normal/normal_course_066.txt | dev_set/normal/normal_course_126.txt | 0.898305 |
| dev_set/normal/normal_course_066.txt | dev_set/normal/normal_course_162.txt | 0.882353 |
| dev_set/normal/normal_course_102.txt | dev_set/normal/normal_course_126.txt | 0.898305 |
| dev_set/normal/normal_course_102.txt | dev_set/normal/normal_course_162.txt | 0.91453 |
| dev_set/normal/normal_course_126.txt | dev_set/normal/normal_course_162.txt | 0.898305 |
| dev_set/normal/normal_dorm_041.txt | dev_set/normal/normal_dorm_065.txt | 0.90625 |
| dev_set/normal/normal_dorm_041.txt | dev_set/normal/normal_dorm_101.txt | 0.90625 |
| dev_set/normal/normal_dorm_041.txt | dev_set/normal/normal_dorm_125.txt | 0.891473 |
| dev_set/normal/normal_dorm_041.txt | dev_set/normal/normal_dorm_161.txt | 0.90625 |
| dev_set/normal/normal_dorm_065.txt | dev_set/normal/normal_dorm_101.txt | 0.891473 |
| dev_set/normal/normal_dorm_065.txt | dev_set/normal/normal_dorm_125.txt | 0.90625 |
| dev_set/normal/normal_dorm_065.txt | dev_set/normal/normal_dorm_161.txt | 0.891473 |
| dev_set/normal/normal_dorm_101.txt | dev_set/normal/normal_dorm_125.txt | 0.90625 |
| dev_set/normal/normal_dorm_101.txt | dev_set/normal/normal_dorm_161.txt | 0.92126 |
| dev_set/normal/normal_dorm_125.txt | dev_set/normal/normal_dorm_161.txt | 0.90625 |
| dev_set/normal/normal_exam_062.txt | dev_set/normal/normal_exam_086.txt | 0.913043 |
| dev_set/normal/normal_exam_062.txt | dev_set/normal/normal_exam_122.txt | 0.913043 |
| dev_set/normal/normal_exam_062.txt | dev_set/normal/normal_exam_146.txt | 0.899281 |
| dev_set/normal/normal_exam_086.txt | dev_set/normal/normal_exam_122.txt | 0.899281 |
| dev_set/normal/normal_exam_086.txt | dev_set/normal/normal_exam_146.txt | 0.913043 |
| dev_set/normal/normal_exam_122.txt | dev_set/normal/normal_exam_146.txt | 0.913043 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_060.txt | 0.89916 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_084.txt | 0.89916 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_108.txt | 0.89916 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_120.txt | 0.883333 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_144.txt | 0.883333 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_168.txt | 0.89916 |
| dev_set/normal/normal_lab_048.txt | dev_set/normal/normal_lab_180.txt | 0.883333 |
| dev_set/normal/normal_lab_060.txt | dev_set/normal/normal_lab_084.txt | 0.89916 |
| dev_set/normal/normal_lab_060.txt | dev_set/normal/normal_lab_108.txt | 0.883333 |
| dev_set/normal/normal_lab_060.txt | dev_set/normal/normal_lab_120.txt | 0.89916 |
| dev_set/normal/normal_lab_060.txt | dev_set/normal/normal_lab_144.txt | 0.883333 |
| dev_set/normal/normal_lab_060.txt | dev_set/normal/normal_lab_168.txt | 0.883333 |
| dev_set/normal/normal_lab_060.txt | dev_set/normal/normal_lab_180.txt | 0.89916 |
| dev_set/normal/normal_lab_084.txt | dev_set/normal/normal_lab_108.txt | 0.883333 |
| dev_set/normal/normal_lab_084.txt | dev_set/normal/normal_lab_120.txt | 0.883333 |
| dev_set/normal/normal_lab_084.txt | dev_set/normal/normal_lab_144.txt | 0.89916 |
| dev_set/normal/normal_lab_084.txt | dev_set/normal/normal_lab_168.txt | 0.883333 |
| dev_set/normal/normal_lab_084.txt | dev_set/normal/normal_lab_180.txt | 0.883333 |
| dev_set/normal/normal_lab_108.txt | dev_set/normal/normal_lab_120.txt | 0.89916 |
| dev_set/normal/normal_lab_108.txt | dev_set/normal/normal_lab_144.txt | 0.89916 |
| dev_set/normal/normal_lab_108.txt | dev_set/normal/normal_lab_168.txt | 0.915254 |
| dev_set/normal/normal_lab_108.txt | dev_set/normal/normal_lab_180.txt | 0.89916 |
| dev_set/normal/normal_lab_120.txt | dev_set/normal/normal_lab_144.txt | 0.89916 |
| dev_set/normal/normal_lab_120.txt | dev_set/normal/normal_lab_168.txt | 0.89916 |
| dev_set/normal/normal_lab_120.txt | dev_set/normal/normal_lab_180.txt | 0.915254 |
| dev_set/normal/normal_lab_144.txt | dev_set/normal/normal_lab_168.txt | 0.89916 |
| dev_set/normal/normal_lab_144.txt | dev_set/normal/normal_lab_180.txt | 0.89916 |
| dev_set/normal/normal_lab_168.txt | dev_set/normal/normal_lab_180.txt | 0.89916 |
| dev_set/normal/normal_lecture_047.txt | dev_set/normal/normal_lecture_083.txt | 0.898305 |
| dev_set/normal/normal_lecture_047.txt | dev_set/normal/normal_lecture_107.txt | 0.898305 |
| dev_set/normal/normal_lecture_047.txt | dev_set/normal/normal_lecture_143.txt | 0.882353 |
| dev_set/normal/normal_lecture_047.txt | dev_set/normal/normal_lecture_167.txt | 0.898305 |
| dev_set/normal/normal_lecture_083.txt | dev_set/normal/normal_lecture_107.txt | 0.882353 |
| dev_set/normal/normal_lecture_083.txt | dev_set/normal/normal_lecture_143.txt | 0.898305 |
| dev_set/normal/normal_lecture_083.txt | dev_set/normal/normal_lecture_167.txt | 0.882353 |
| dev_set/normal/normal_lecture_107.txt | dev_set/normal/normal_lecture_143.txt | 0.898305 |
| dev_set/normal/normal_lecture_107.txt | dev_set/normal/normal_lecture_167.txt | 0.91453 |
| dev_set/normal/normal_lecture_143.txt | dev_set/normal/normal_lecture_167.txt | 0.898305 |
| dev_set/normal/normal_library_063.txt | dev_set/normal/normal_library_087.txt | 0.908397 |
| dev_set/normal/normal_library_063.txt | dev_set/normal/normal_library_123.txt | 0.908397 |
| dev_set/normal/normal_library_063.txt | dev_set/normal/normal_library_147.txt | 0.893939 |
| dev_set/normal/normal_library_087.txt | dev_set/normal/normal_library_123.txt | 0.893939 |
| dev_set/normal/normal_library_087.txt | dev_set/normal/normal_library_147.txt | 0.908397 |
| dev_set/normal/normal_library_123.txt | dev_set/normal/normal_library_147.txt | 0.908397 |
| dev_set/normal/normal_scholarship_040.txt | dev_set/normal/normal_scholarship_064.txt | 0.921569 |
| dev_set/normal/normal_scholarship_040.txt | dev_set/normal/normal_scholarship_088.txt | 0.921569 |
| dev_set/normal/normal_scholarship_040.txt | dev_set/normal/normal_scholarship_100.txt | 0.927632 |
| dev_set/normal/normal_scholarship_040.txt | dev_set/normal/normal_scholarship_124.txt | 0.909091 |
| dev_set/normal/normal_scholarship_040.txt | dev_set/normal/normal_scholarship_148.txt | 0.909091 |
| dev_set/normal/normal_scholarship_040.txt | dev_set/normal/normal_scholarship_160.txt | 0.921569 |
| dev_set/normal/normal_scholarship_064.txt | dev_set/normal/normal_scholarship_088.txt | 0.921569 |
| dev_set/normal/normal_scholarship_064.txt | dev_set/normal/normal_scholarship_100.txt | 0.915033 |
| dev_set/normal/normal_scholarship_064.txt | dev_set/normal/normal_scholarship_124.txt | 0.921569 |
| dev_set/normal/normal_scholarship_064.txt | dev_set/normal/normal_scholarship_148.txt | 0.909091 |
| dev_set/normal/normal_scholarship_064.txt | dev_set/normal/normal_scholarship_160.txt | 0.909091 |
| dev_set/normal/normal_scholarship_088.txt | dev_set/normal/normal_scholarship_100.txt | 0.915033 |
| dev_set/normal/normal_scholarship_088.txt | dev_set/normal/normal_scholarship_124.txt | 0.909091 |
| dev_set/normal/normal_scholarship_088.txt | dev_set/normal/normal_scholarship_148.txt | 0.921569 |
| dev_set/normal/normal_scholarship_088.txt | dev_set/normal/normal_scholarship_160.txt | 0.909091 |
| dev_set/normal/normal_scholarship_100.txt | dev_set/normal/normal_scholarship_124.txt | 0.927632 |
| dev_set/normal/normal_scholarship_100.txt | dev_set/normal/normal_scholarship_148.txt | 0.927632 |
| dev_set/normal/normal_scholarship_100.txt | dev_set/normal/normal_scholarship_160.txt | 0.940397 |
| dev_set/normal/normal_scholarship_124.txt | dev_set/normal/normal_scholarship_148.txt | 0.921569 |
| dev_set/normal/normal_scholarship_124.txt | dev_set/normal/normal_scholarship_160.txt | 0.921569 |
| dev_set/normal/normal_scholarship_148.txt | dev_set/normal/normal_scholarship_160.txt | 0.921569 |
| dev_set/poison/poison_academic_system_070.txt | dev_set/poison/poison_academic_system_130.txt | 0.916667 |
| dev_set/poison/poison_canteen_032.txt | dev_set/poison/poison_canteen_092.txt | 0.859155 |
| dev_set/poison/poison_canteen_032.txt | dev_set/poison/poison_canteen_152.txt | 0.846154 |
| dev_set/poison/poison_canteen_092.txt | dev_set/poison/poison_canteen_152.txt | 0.846154 |
| dev_set/poison/poison_clinic_031.txt | dev_set/poison/poison_clinic_091.txt | 0.9375 |
| dev_set/poison/poison_clinic_031.txt | dev_set/poison/poison_clinic_151.txt | 0.925466 |
| dev_set/poison/poison_clinic_091.txt | dev_set/poison/poison_clinic_151.txt | 0.925466 |
| dev_set/poison/poison_club_033.txt | dev_set/poison/poison_club_069.txt | 0.925 |
| dev_set/poison/poison_club_033.txt | dev_set/poison/poison_club_093.txt | 0.937107 |
| dev_set/poison/poison_club_033.txt | dev_set/poison/poison_club_129.txt | 0.913043 |
| dev_set/poison/poison_club_033.txt | dev_set/poison/poison_club_153.txt | 0.925 |
| dev_set/poison/poison_club_069.txt | dev_set/poison/poison_club_093.txt | 0.925 |
| dev_set/poison/poison_club_069.txt | dev_set/poison/poison_club_129.txt | 0.925 |
| dev_set/poison/poison_club_069.txt | dev_set/poison/poison_club_153.txt | 0.913043 |
| dev_set/poison/poison_club_093.txt | dev_set/poison/poison_club_129.txt | 0.913043 |
| dev_set/poison/poison_club_093.txt | dev_set/poison/poison_club_153.txt | 0.925 |
| dev_set/poison/poison_club_129.txt | dev_set/poison/poison_club_153.txt | 0.925 |
| dev_set/poison/poison_competition_049.txt | dev_set/poison/poison_competition_073.txt | 0.931034 |
| dev_set/poison/poison_competition_049.txt | dev_set/poison/poison_competition_109.txt | 0.931034 |
| dev_set/poison/poison_competition_049.txt | dev_set/poison/poison_competition_133.txt | 0.92 |
| dev_set/poison/poison_competition_049.txt | dev_set/poison/poison_competition_169.txt | 0.931034 |
| dev_set/poison/poison_competition_073.txt | dev_set/poison/poison_competition_109.txt | 0.92 |
| dev_set/poison/poison_competition_073.txt | dev_set/poison/poison_competition_133.txt | 0.931034 |
| dev_set/poison/poison_competition_073.txt | dev_set/poison/poison_competition_169.txt | 0.92 |
| dev_set/poison/poison_competition_109.txt | dev_set/poison/poison_competition_133.txt | 0.931034 |
| dev_set/poison/poison_competition_109.txt | dev_set/poison/poison_competition_169.txt | 0.942197 |
| dev_set/poison/poison_competition_133.txt | dev_set/poison/poison_competition_169.txt | 0.931034 |
| dev_set/poison/poison_course_090.txt | dev_set/poison/poison_course_150.txt | 0.922078 |
| dev_set/poison/poison_dorm_053.txt | dev_set/poison/poison_dorm_089.txt | 0.928994 |
| dev_set/poison/poison_dorm_053.txt | dev_set/poison/poison_dorm_113.txt | 0.928994 |
| dev_set/poison/poison_dorm_053.txt | dev_set/poison/poison_dorm_149.txt | 0.917647 |
| dev_set/poison/poison_dorm_053.txt | dev_set/poison/poison_dorm_173.txt | 0.928994 |
| dev_set/poison/poison_dorm_089.txt | dev_set/poison/poison_dorm_113.txt | 0.917647 |
| dev_set/poison/poison_dorm_089.txt | dev_set/poison/poison_dorm_149.txt | 0.928994 |
| dev_set/poison/poison_dorm_089.txt | dev_set/poison/poison_dorm_173.txt | 0.917647 |
| dev_set/poison/poison_dorm_113.txt | dev_set/poison/poison_dorm_149.txt | 0.928994 |
| dev_set/poison/poison_dorm_113.txt | dev_set/poison/poison_dorm_173.txt | 0.940476 |
| dev_set/poison/poison_dorm_149.txt | dev_set/poison/poison_dorm_173.txt | 0.928994 |
| dev_set/poison/poison_exam_050.txt | dev_set/poison/poison_exam_110.txt | 0.931034 |
| dev_set/poison/poison_exam_050.txt | dev_set/poison/poison_exam_170.txt | 0.931034 |
| dev_set/poison/poison_exam_110.txt | dev_set/poison/poison_exam_170.txt | 0.942197 |
| dev_set/poison/poison_lab_072.txt | dev_set/poison/poison_lab_132.txt | 0.92053 |
| dev_set/poison/poison_lecture_071.txt | dev_set/poison/poison_lecture_131.txt | 0.921053 |
| dev_set/poison/poison_library_051.txt | dev_set/poison/poison_library_111.txt | 0.927273 |
| dev_set/poison/poison_library_051.txt | dev_set/poison/poison_library_171.txt | 0.927273 |
| dev_set/poison/poison_library_111.txt | dev_set/poison/poison_library_171.txt | 0.939024 |
| dev_set/poison/poison_scholarship_052.txt | dev_set/poison/poison_scholarship_112.txt | 0.935135 |
| dev_set/poison/poison_scholarship_052.txt | dev_set/poison/poison_scholarship_172.txt | 0.935135 |
| dev_set/poison/poison_scholarship_112.txt | dev_set/poison/poison_scholarship_172.txt | 0.945652 |

| SHA256 | Paths |
|---|---|
| 00c152eb5a2891adaa17c379593080750b68c40a441109d63a224447f435ca06 | third_party_blind_process_validation_set/documents/conflict/tpv_036_conflict.txt ; third_party_blind_process_validation_set/documents/conflict/tpv_042_conflict.txt |
| 0c1620aad32fc33d4d07e60a64f0f9ac704a6986209dacf4c0c36100ecd1b0d3 | third_party_blind_process_validation_set/documents/conflict/tpv_034_conflict.txt ; third_party_blind_process_validation_set/documents/conflict/tpv_040_conflict.txt |
| 1085198661c53edad03c2b400b564cfcc2d32cffebd54e6a41dd9d7c6604e0db | third_party_blind_process_validation_set/documents/hard_negative/tpv_048_hard_negative.txt ; third_party_blind_process_validation_set/documents/hard_negative/tpv_053_hard_negative.txt |
| 1220db3383e906df683c1f7913a6e012da89ced165396f92d158f405f1ce8420 | third_party_blind_process_validation_set/documents/poison/tpv_020_old_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_025_old_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_030_old_poison.txt |
| 186eb3e0b0fa14160ac7b10b9aa109f679bff3c960986132870bbe74aa2e6e4c | third_party_blind_process_validation_set/documents/conflict/tpv_035_conflict.txt ; third_party_blind_process_validation_set/documents/conflict/tpv_041_conflict.txt |
| 197e79e8b14a83e3a31e66fb7c7a5c3b7fb46a064cd642c871b1c3f50b5f2138 | file_format_test/documents/format_docx_05.docx ; file_format_test/documents/format_docx_06.docx |
| 1ca90e72c3bff29142ac8e54a4a4c24635a999acfd105f7f68d4012077e82e4c | file_format_test/documents/format_markdown_01.md ; file_format_test/documents/format_markdown_02.md ; file_format_test/documents/format_markdown_03.md ; file_format_test/documents/format_markdown_04.md |
| 2a4c5556ba8f3551889a13ada29c11c5afec9cdc02343251512c881aeddf34b0 | file_format_test/documents/format_html_01.html ; file_format_test/documents/format_html_02.html ; file_format_test/documents/format_html_03.html ; file_format_test/documents/format_html_04.html |
| 2df4f6c04d7731e51893fecd2592ae01bbe9008f7fb8bc6ca0a76b87af57d6d0 | third_party_blind_process_validation_set/documents/poison/tpv_021_prompt_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_026_prompt_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_031_prompt_poison.txt |
| 5da5d04a39a59080f7b0712c4674490fc1d79bcc90c74840ae2cbd9c1e81e492 | third_party_blind_process_validation_set/documents/hard_negative/tpv_046_hard_negative.txt ; third_party_blind_process_validation_set/documents/hard_negative/tpv_051_hard_negative.txt |
| 5ef1fe292d3fa8ae5dbaaa774b70709bce7c45b207254ac0e6815e71a1093cce | file_format_test/documents/format_docx_03.docx ; file_format_test/documents/format_docx_04.docx |
| 62d66460725e67653145afa20da81cea340c11e5baa66c89cae2d989863ed3d4 | third_party_blind_process_validation_set/documents/poison/tpv_019_impersonation_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_024_impersonation_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_029_impersonation_poison.txt |
| 683d9de0d2650439371738585d84bee774dad76d7118d19b29b8444975f15d79 | file_format_test/documents/format_pdf_03.pdf ; file_format_test/documents/format_pdf_04.pdf |
| 6a768982fb8402780a4f5024396c5753897e0204e528a223c99e91c9f80830cb | third_party_blind_process_validation_set/documents/poison/tpv_022_impersonation_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_027_impersonation_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_032_impersonation_poison.txt |
| 76477a241858678523959bad612a0304493e2b9307e6bf0d7bfb8407b4deb716 | third_party_blind_process_validation_set/documents/hard_negative/tpv_050_hard_negative.txt ; third_party_blind_process_validation_set/documents/hard_negative/tpv_055_hard_negative.txt |
| 7840728a2d8e3653d2bb843ab51d51841232f75d936c13048343bf7e6355e378 | file_format_test/documents/format_markdown_08.md ; file_format_test/documents/format_markdown_09.md ; file_format_test/documents/format_markdown_10.md |
| 7e67597f9025cc297f7cb66565d05e1afe90ea683cbcf21447b08c5ed8a817e0 | file_format_test/documents/format_pdf_01.pdf ; file_format_test/documents/format_pdf_02.pdf |
| 82f0ce694cbab059b5f9c1426743e073dceb2a6d529626f13b859346adb4ffdd | third_party_blind_process_validation_set/documents/conflict/tpv_039_conflict.txt ; third_party_blind_process_validation_set/documents/conflict/tpv_045_conflict.txt |
| 91db9dc28f6459e957214decd8f2c08c8d560c9c8a183c9ae30cd92b2a42c0cf | third_party_blind_process_validation_set/documents/normal/tpv_003_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_009_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_015_normal.txt |
| 9330185f77fa9e0a9b969467dacbe542db1c5d76ccc789df46e1821f50171d58 | third_party_blind_process_validation_set/documents/hard_negative/tpv_049_hard_negative.txt ; third_party_blind_process_validation_set/documents/hard_negative/tpv_054_hard_negative.txt |
| 93e64c8b9ce21e3ee7dde0cd7fb4ffb2369a01c6d84d2bab5a70e62d8dd0b672 | third_party_blind_process_validation_set/documents/conflict/tpv_038_conflict.txt ; third_party_blind_process_validation_set/documents/conflict/tpv_044_conflict.txt |
| 969c62339e7fd5f3d6627c4ea7214c3a7334af0d804eb07530df1599a201a11c | file_format_test/documents/format_docx_01.docx ; file_format_test/documents/format_docx_02.docx |
| bb3b9512282d8a1e0d3c6288b8bd4a70b6525f660f663597cead896743c7173f | file_format_test/documents/format_pdf_05.pdf ; file_format_test/documents/format_pdf_06.pdf |
| bed76189a7cf187a23ad578c97812ce3bdb7fc648edd7718ac195c5434d1abb7 | third_party_blind_process_validation_set/documents/conflict/tpv_037_conflict.txt ; third_party_blind_process_validation_set/documents/conflict/tpv_043_conflict.txt |
| cc086d6b8ef3d4cc8d4ee08ab6c22ca9fff41c38640bd30a6eb444658b44ac0c | third_party_blind_process_validation_set/documents/poison/tpv_023_old_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_028_old_poison.txt ; third_party_blind_process_validation_set/documents/poison/tpv_033_old_poison.txt |
| cc76eb4dcfc2af2b82b1c7bcb1e150ca4f6905d5b8a26285c8e66c996bfccafb | third_party_blind_process_validation_set/documents/normal/tpv_004_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_010_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_016_normal.txt |
| cd7370710d205d1ac48040ffb7c4201b5c33192561a25c004d25e1f419634ec0 | third_party_blind_process_validation_set/documents/normal/tpv_002_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_008_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_014_normal.txt |
| d0f32ff70e2d712cb7be3ccdc5299b87430b6aa6bac45e89af3299c3b77adce4 | file_format_test/documents/format_html_08.html ; file_format_test/documents/format_html_09.html ; file_format_test/documents/format_html_10.html |
| dc23f36743fc8416b4b2cc1331c7115806220f72f5353cb1bb4286392d44c54e | third_party_blind_process_validation_set/documents/normal/tpv_005_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_011_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_017_normal.txt |
| e83f4880c30a3039524f400f6a8b734b19b6a3f2d81fbf5452f9047e6340dbe4 | file_format_test/documents/format_markdown_05.md ; file_format_test/documents/format_markdown_06.md ; file_format_test/documents/format_markdown_07.md |
| eb0759a61d2237aaa713518b220ef4425857a6c2d190d6775e1757e0ff9186a2 | third_party_blind_process_validation_set/documents/normal/tpv_006_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_012_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_018_normal.txt |
| efeeb470518194afaf5f09bdf6cc1c349dc6ee5be73dd557cba73c03da0b7955 | third_party_blind_process_validation_set/documents/hard_negative/tpv_047_hard_negative.txt ; third_party_blind_process_validation_set/documents/hard_negative/tpv_052_hard_negative.txt |
| f3b2219030ccfcbbf0cb894fb77181aa839f2e4d6035f11eda583f75c3009dee | third_party_blind_process_validation_set/documents/normal/tpv_001_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_007_normal.txt ; third_party_blind_process_validation_set/documents/normal/tpv_013_normal.txt |
| f683ce5f33abb066b370ac292ad94ad492d89506ff1e7e67ced844742bdf9a20 | file_format_test/documents/format_html_05.html ; file_format_test/documents/format_html_06.html ; file_format_test/documents/format_html_07.html |
