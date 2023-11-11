#! /usr/bin/env python3
# coding: utf-8

"""
Validation des modèles
"""

import pickle
import re
import sys
import math
import csv
import langdetect
import nltk
import stanza
import tqdm
import main_stats
import pandas as pd
from nltk.corpus import stopwords
from traitement import nettoyage
from traitement import stats
from databases import psql_cmd
from main_nlp import lemmatise
from databases.psql_db import secrets as ps_secrets
from sklearn.metrics import precision_recall_fscore_support as score


if __name__ == '__main__':
    print("=== Validation des modèles ===")
    alg_decision_tree = pickle.load(open('./models/decision_tree_spam.sav', 'rb'))
    alg_svm = pickle.load(open('./models/svm_spam.sav', 'rb'))

    nltk.download("stopwords")
    en_stopwd = set(stopwords.words('english'))
    pipe = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    pat = re.compile(r'\w+')

    file = 'dev_dataset/validation/spam_ham_dataset.csv'
    # with open(file, 'rb') as csvfile:
    #     csv_lines = csvfile.readlines()[1:]
    reader = csv.DictReader(open(file))

    sms_data_init = []
    id_message = 0
    for line in tqdm.tqdm(reader,
                          desc="-- Traitement initial des messages...",
                          leave=False,
                          file=sys.stdout,
                          ascii=True):
        # infos = line.decode('utf-8', 'ignore').split(',')

        # Adapter selon le dataset de validation
        message = '\n'.join(line['text'].splitlines()[1:])
        categorie = 1 if line['label'] == 'spam' else 2

        # Nettoyage initial
        corp, liens = nettoyage.clear_texte_init(message)
        if not corp:
            continue

        try:
            lang = langdetect.detect(corp)
            if lang != 'en':
                continue
        except langdetect.lang_detect_exception.LangDetectException:
            continue

        new_entry = {
            'id_message': id_message,
            'categorie': categorie,
            'message': corp}
        for key, value in liens.items():
            new_entry[key.lower()] = value

        if new_entry not in sms_data_init:
            sms_data_init.append(new_entry)
            id_message += 1
    print("-- Traitement initial des messages... OK")

    # Feature engineering
    for entry in tqdm.tqdm(sms_data_init,
                           desc='-- Traitement statistique...',
                           leave=False,
                           file=sys.stdout,
                           ascii=True):
        id_mes = entry['id_message']
        message = entry['message']
        entry.update(main_stats.stats_ponct(id_mes, message))
        entry.update(main_stats.stats_mot(id_mes, message))
        entry.update(main_stats.stats_zipf(id_mes, message))
        entry.update(main_stats.stats_hapax(id_mes, message))
    print("-- Traitement statistique... OK")

    # Vectorisation
    psql_cli = psql_cmd.connect_db(user=ps_secrets.owner,
                                   passwd=ps_secrets.owner_pw,
                                   host=ps_secrets.host,
                                   port=ps_secrets.port,
                                   dbname="mail_features_prod")
    query = "SELECT COUNT(id_message) from nlp_status WHERE success = true"
    nb_doc = psql_cmd.exec_query(psql_cli, query)[0][0]

    query = ("SELECT m.mot, a.label, m.freq_doc_all FROM tfidf_assoc as a "
             "JOIN mot_corpus AS m ON a.id_mot = m.id_mot")
    base_vector = psql_cmd.exec_query(psql_cli, query)

    psql_cli.close()

    for entry in tqdm.tqdm(sms_data_init,
                           desc='-- Vectorisation...',
                           leave=False,
                           file=sys.stdout,
                           ascii=True):
        try:
            freq_bag = stats.frequence_mot(lemmatise(entry['message'], en_stopwd, pipe, pat))
        except TypeError:
            sms_data_init.pop(sms_data_init.index(entry))
            continue

        for cellule in base_vector:
            mot, label, doc_freq = cellule
            vect_value = 0 if mot not in freq_bag else freq_bag[mot] * math.log(nb_doc/doc_freq)
            entry.update({label: vect_value})

    print('-- Vectorisation... OK')

    print('== Validation')
    validation_df = pd.DataFrame(sms_data_init)
    validation_cat = validation_df['categorie']
    validation_df.drop(['categorie', 'id_message', 'message', 'tel', 'virgule', 'tabulation',
                        'espace', 'ligne_vide', 'mots_uniques'], axis=1, inplace=True)
    cols_order = ['constante', 'coefficient', 'tx_erreur', 'mots', 'char_min', 'char_maj',
                  'mot_maj', 'mot_cap', 'url', 'mail', 'nombre', 'prix', 'h_nombre', 'ratio_unique',
                  'ratio_texte', 'point', 'exclamation', 'interrogation', 'ligne', 'feat_mot_0',
                  'feat_mot_1', 'feat_mot_2', 'feat_mot_3', 'feat_mot_4', 'feat_mot_5',
                  'feat_mot_6', 'feat_mot_7', 'feat_mot_8', 'feat_mot_9', 'feat_mot_10',
                  'feat_mot_11', 'feat_mot_12', 'feat_mot_13', 'feat_mot_14', 'feat_mot_15',
                  'feat_mot_16', 'feat_mot_17', 'feat_mot_18', 'feat_mot_19', 'feat_mot_20',
                  'feat_mot_21', 'feat_mot_22', 'feat_mot_23', 'feat_mot_24', 'feat_mot_25',
                  'feat_mot_26', 'feat_mot_27', 'feat_mot_28', 'feat_mot_29', 'feat_mot_30',
                  'feat_mot_31', 'feat_mot_32', 'feat_mot_33', 'feat_mot_34', 'feat_mot_35',
                  'feat_mot_36', 'feat_mot_37', 'feat_mot_38', 'feat_mot_39', 'feat_mot_40',
                  'feat_mot_41', 'feat_mot_42', 'feat_mot_43', 'feat_mot_44', 'feat_mot_45',
                  'feat_mot_46', 'feat_mot_47', 'feat_mot_48', 'feat_mot_49', 'feat_mot_50',
                  'feat_mot_51', 'feat_mot_52', 'feat_mot_53', 'feat_mot_54', 'feat_mot_55',
                  'feat_mot_56', 'feat_mot_57', 'feat_mot_58', 'feat_mot_59', 'feat_mot_60',
                  'feat_mot_61', 'feat_mot_62', 'feat_mot_63', 'feat_mot_64', 'feat_mot_65',
                  'feat_mot_66', 'feat_mot_67', 'feat_mot_68', 'feat_mot_69', 'feat_mot_70',
                  'feat_mot_71', 'feat_mot_72', 'feat_mot_73', 'feat_mot_74', 'feat_mot_75',
                  'feat_mot_76', 'feat_mot_77', 'feat_mot_78', 'feat_mot_79', 'feat_mot_80',
                  'feat_mot_81', 'feat_mot_82', 'feat_mot_83', 'feat_mot_84', 'feat_mot_85',
                  'feat_mot_86', 'feat_mot_87', 'feat_mot_88', 'feat_mot_89', 'feat_mot_90',
                  'feat_mot_91', 'feat_mot_92', 'feat_mot_93', 'feat_mot_94', 'feat_mot_95',
                  'feat_mot_96', 'feat_mot_97', 'feat_mot_98', 'feat_mot_99', 'feat_mot_100',
                  'feat_mot_101', 'feat_mot_102', 'feat_mot_103', 'feat_mot_104', 'feat_mot_105',
                  'feat_mot_106', 'feat_mot_107', 'feat_mot_108', 'feat_mot_109', 'feat_mot_110',
                  'feat_mot_111', 'feat_mot_112', 'feat_mot_113', 'feat_mot_114', 'feat_mot_115',
                  'feat_mot_116', 'feat_mot_117', 'feat_mot_118', 'feat_mot_119', 'feat_mot_120',
                  'feat_mot_121', 'feat_mot_122', 'feat_mot_123', 'feat_mot_124', 'feat_mot_125',
                  'feat_mot_126', 'feat_mot_127', 'feat_mot_128', 'feat_mot_129', 'feat_mot_130',
                  'feat_mot_131', 'feat_mot_132', 'feat_mot_133', 'feat_mot_134', 'feat_mot_135',
                  'feat_mot_136', 'feat_mot_137', 'feat_mot_138', 'feat_mot_139', 'feat_mot_140',
                  'feat_mot_141', 'feat_mot_142', 'feat_mot_143', 'feat_mot_144', 'feat_mot_145',
                  'feat_mot_146', 'feat_mot_147', 'feat_mot_148', 'feat_mot_149', 'feat_mot_150',
                  'feat_mot_151', 'feat_mot_152', 'feat_mot_153', 'feat_mot_154', 'feat_mot_155',
                  'feat_mot_156', 'feat_mot_157', 'feat_mot_158', 'feat_mot_159', 'feat_mot_160',
                  'feat_mot_161', 'feat_mot_162', 'feat_mot_163', 'feat_mot_164', 'feat_mot_165',
                  'feat_mot_166', 'feat_mot_167', 'feat_mot_168', 'feat_mot_169', 'feat_mot_170',
                  'feat_mot_171', 'feat_mot_172', 'feat_mot_173', 'feat_mot_174', 'feat_mot_175',
                  'feat_mot_176', 'feat_mot_177', 'feat_mot_178', 'feat_mot_179', 'feat_mot_180',
                  'feat_mot_181', 'feat_mot_182', 'feat_mot_183', 'feat_mot_184', 'feat_mot_185',
                  'feat_mot_186', 'feat_mot_187', 'feat_mot_188', 'feat_mot_189', 'feat_mot_190',
                  'feat_mot_191', 'feat_mot_192', 'feat_mot_193', 'feat_mot_194', 'feat_mot_195',
                  'feat_mot_196', 'feat_mot_197', 'feat_mot_198', 'feat_mot_199', 'feat_mot_200',
                  'feat_mot_201', 'feat_mot_202', 'feat_mot_203', 'feat_mot_204', 'feat_mot_205',
                  'feat_mot_206', 'feat_mot_207', 'feat_mot_208', 'feat_mot_209', 'feat_mot_210',
                  'feat_mot_211', 'feat_mot_212', 'feat_mot_213', 'feat_mot_214', 'feat_mot_215',
                  'feat_mot_216', 'feat_mot_217', 'feat_mot_218', 'feat_mot_219', 'feat_mot_220',
                  'feat_mot_221', 'feat_mot_222', 'feat_mot_223', 'feat_mot_224', 'feat_mot_225',
                  'feat_mot_226', 'feat_mot_227', 'feat_mot_228', 'feat_mot_229', 'feat_mot_230',
                  'feat_mot_231', 'feat_mot_232', 'feat_mot_233', 'feat_mot_234', 'feat_mot_235',
                  'feat_mot_236', 'feat_mot_237', 'feat_mot_238', 'feat_mot_239', 'feat_mot_240',
                  'feat_mot_241', 'feat_mot_242', 'feat_mot_243', 'feat_mot_244', 'feat_mot_245',
                  'feat_mot_246', 'feat_mot_247', 'feat_mot_248', 'feat_mot_249', 'feat_mot_250',
                  'feat_mot_251', 'feat_mot_252', 'feat_mot_253', 'feat_mot_254', 'feat_mot_255',
                  'feat_mot_256', 'feat_mot_257', 'feat_mot_258', 'feat_mot_259', 'feat_mot_260',
                  'feat_mot_261', 'feat_mot_262', 'feat_mot_263', 'feat_mot_264', 'feat_mot_265',
                  'feat_mot_266', 'feat_mot_267', 'feat_mot_268', 'feat_mot_269', 'feat_mot_270',
                  'feat_mot_271', 'feat_mot_272', 'feat_mot_273', 'feat_mot_274', 'feat_mot_275',
                  'feat_mot_276', 'feat_mot_277', 'feat_mot_278', 'feat_mot_279', 'feat_mot_280',
                  'feat_mot_281', 'feat_mot_282', 'feat_mot_283', 'feat_mot_284', 'feat_mot_285',
                  'feat_mot_286', 'feat_mot_287', 'feat_mot_288', 'feat_mot_289', 'feat_mot_290',
                  'feat_mot_291', 'feat_mot_292', 'feat_mot_293', 'feat_mot_294', 'feat_mot_295',
                  'feat_mot_296', 'feat_mot_297', 'feat_mot_298', 'feat_mot_299', 'feat_mot_300',
                  'feat_mot_301', 'feat_mot_302', 'feat_mot_303', 'feat_mot_304', 'feat_mot_305',
                  'feat_mot_306', 'feat_mot_307', 'feat_mot_308', 'feat_mot_309', 'feat_mot_310',
                  'feat_mot_311', 'feat_mot_312', 'feat_mot_313', 'feat_mot_314', 'feat_mot_315',
                  'feat_mot_316', 'feat_mot_317', 'feat_mot_318', 'feat_mot_319', 'feat_mot_320',
                  'feat_mot_321', 'feat_mot_322', 'feat_mot_323', 'feat_mot_324', 'feat_mot_325',
                  'feat_mot_326', 'feat_mot_327', 'feat_mot_328', 'feat_mot_329', 'feat_mot_330',
                  'feat_mot_331', 'feat_mot_332', 'feat_mot_333', 'feat_mot_334', 'feat_mot_335',
                  'feat_mot_336', 'feat_mot_337', 'feat_mot_338', 'feat_mot_339', 'feat_mot_340',
                  'feat_mot_341', 'feat_mot_342', 'feat_mot_343', 'feat_mot_344', 'feat_mot_345',
                  'feat_mot_346', 'feat_mot_347', 'feat_mot_348', 'feat_mot_349', 'feat_mot_350',
                  'feat_mot_351', 'feat_mot_352', 'feat_mot_353', 'feat_mot_354', 'feat_mot_355',
                  'feat_mot_356', 'feat_mot_357', 'feat_mot_358', 'feat_mot_359', 'feat_mot_360',
                  'feat_mot_361', 'feat_mot_362', 'feat_mot_363', 'feat_mot_364', 'feat_mot_365',
                  'feat_mot_366', 'feat_mot_367', 'feat_mot_368', 'feat_mot_369', 'feat_mot_370',
                  'feat_mot_371', 'feat_mot_372', 'feat_mot_373', 'feat_mot_374', 'feat_mot_375',
                  'feat_mot_376', 'feat_mot_377', 'feat_mot_378', 'feat_mot_379', 'feat_mot_380',
                  'feat_mot_381', 'feat_mot_382', 'feat_mot_383', 'feat_mot_384', 'feat_mot_385',
                  'feat_mot_386', 'feat_mot_387', 'feat_mot_388', 'feat_mot_389', 'feat_mot_390',
                  'feat_mot_391', 'feat_mot_392', 'feat_mot_393', 'feat_mot_394', 'feat_mot_395',
                  'feat_mot_396', 'feat_mot_397', 'feat_mot_398', 'feat_mot_399', 'feat_mot_400',
                  'feat_mot_401', 'feat_mot_402', 'feat_mot_403', 'feat_mot_404', 'feat_mot_405',
                  'feat_mot_406', 'feat_mot_407', 'feat_mot_408', 'feat_mot_409', 'feat_mot_410',
                  'feat_mot_411', 'feat_mot_412', 'feat_mot_413', 'feat_mot_414', 'feat_mot_415',
                  'feat_mot_416', 'feat_mot_417', 'feat_mot_418', 'feat_mot_419', 'feat_mot_420',
                  'feat_mot_421', 'feat_mot_422', 'feat_mot_423', 'feat_mot_424', 'feat_mot_425',
                  'feat_mot_426', 'feat_mot_427', 'feat_mot_428', 'feat_mot_429', 'feat_mot_430',
                  'feat_mot_431', 'feat_mot_432', 'feat_mot_433', 'feat_mot_434', 'feat_mot_435',
                  'feat_mot_436', 'feat_mot_437', 'feat_mot_438', 'feat_mot_439', 'feat_mot_440',
                  'feat_mot_441', 'feat_mot_442', 'feat_mot_443', 'feat_mot_444', 'feat_mot_445',
                  'feat_mot_446', 'feat_mot_447', 'feat_mot_448', 'feat_mot_449', 'feat_mot_450',
                  'feat_mot_451', 'feat_mot_452', 'feat_mot_453', 'feat_mot_454', 'feat_mot_455',
                  'feat_mot_456', 'feat_mot_457', 'feat_mot_458', 'feat_mot_459', 'feat_mot_460',
                  'feat_mot_461', 'feat_mot_462', 'feat_mot_463', 'feat_mot_464', 'feat_mot_465',
                  'feat_mot_466', 'feat_mot_467', 'feat_mot_468', 'feat_mot_469', 'feat_mot_470',
                  'feat_mot_471', 'feat_mot_472', 'feat_mot_473', 'feat_mot_474', 'feat_mot_475',
                  'feat_mot_476', 'feat_mot_477', 'feat_mot_478', 'feat_mot_479', 'feat_mot_480',
                  'feat_mot_481', 'feat_mot_482', 'feat_mot_483', 'feat_mot_484', 'feat_mot_485',
                  'feat_mot_486', 'feat_mot_487', 'feat_mot_488', 'feat_mot_489', 'feat_mot_490',
                  'feat_mot_491', 'feat_mot_492', 'feat_mot_493', 'feat_mot_494', 'feat_mot_495',
                  'feat_mot_496', 'feat_mot_497', 'feat_mot_498', 'feat_mot_499', 'feat_mot_500',
                  'feat_mot_501', 'feat_mot_502', 'feat_mot_503', 'feat_mot_504', 'feat_mot_505',
                  'feat_mot_506', 'feat_mot_507', 'feat_mot_508', 'feat_mot_509', 'feat_mot_510',
                  'feat_mot_511', 'feat_mot_512', 'feat_mot_513', 'feat_mot_514', 'feat_mot_515',
                  'feat_mot_516', 'feat_mot_517', 'feat_mot_518', 'feat_mot_519', 'feat_mot_520',
                  'feat_mot_521', 'feat_mot_522', 'feat_mot_523', 'feat_mot_524', 'feat_mot_525',
                  'feat_mot_526', 'feat_mot_527', 'feat_mot_528', 'feat_mot_529', 'feat_mot_530',
                  'feat_mot_531', 'feat_mot_532', 'feat_mot_533', 'feat_mot_534', 'feat_mot_535',
                  'feat_mot_536', 'feat_mot_537', 'feat_mot_538', 'feat_mot_539', 'feat_mot_540',
                  'feat_mot_541', 'feat_mot_542', 'feat_mot_543', 'feat_mot_544', 'feat_mot_545',
                  'feat_mot_546', 'feat_mot_547', 'feat_mot_548', 'feat_mot_549', 'feat_mot_550',
                  'feat_mot_551', 'feat_mot_552', 'feat_mot_553', 'feat_mot_554', 'feat_mot_555',
                  'feat_mot_556', 'feat_mot_557', 'feat_mot_558', 'feat_mot_559', 'feat_mot_560',
                  'feat_mot_561', 'feat_mot_562', 'feat_mot_563', 'feat_mot_564', 'feat_mot_565',
                  'feat_mot_566', 'feat_mot_567', 'feat_mot_568', 'feat_mot_569', 'feat_mot_570',
                  'feat_mot_571', 'feat_mot_572', 'feat_mot_573', 'feat_mot_574', 'feat_mot_575',
                  'feat_mot_576', 'feat_mot_577', 'feat_mot_578', 'feat_mot_579', 'feat_mot_580',
                  'feat_mot_581', 'feat_mot_582', 'feat_mot_583', 'feat_mot_584', 'feat_mot_585',
                  'feat_mot_586', 'feat_mot_587', 'feat_mot_588', 'feat_mot_589', 'feat_mot_590',
                  'feat_mot_591', 'feat_mot_592', 'feat_mot_593', 'feat_mot_594', 'feat_mot_595',
                  'feat_mot_596', 'feat_mot_597', 'feat_mot_598', 'feat_mot_599', 'feat_mot_600',
                  'feat_mot_601', 'feat_mot_602', 'feat_mot_603', 'feat_mot_604', 'feat_mot_605',
                  'feat_mot_606', 'feat_mot_607', 'feat_mot_608', 'feat_mot_609', 'feat_mot_610',
                  'feat_mot_611', 'feat_mot_612', 'feat_mot_613', 'feat_mot_614', 'feat_mot_615',
                  'feat_mot_616', 'feat_mot_617', 'feat_mot_618', 'feat_mot_619', 'feat_mot_620',
                  'feat_mot_621', 'feat_mot_622', 'feat_mot_623', 'feat_mot_624', 'feat_mot_625',
                  'feat_mot_626', 'feat_mot_627', 'feat_mot_628', 'feat_mot_629', 'feat_mot_630',
                  'feat_mot_631', 'feat_mot_632', 'feat_mot_633', 'feat_mot_634', 'feat_mot_635',
                  'feat_mot_636', 'feat_mot_637', 'feat_mot_638', 'feat_mot_639', 'feat_mot_640',
                  'feat_mot_641', 'feat_mot_642', 'feat_mot_643', 'feat_mot_644', 'feat_mot_645',
                  'feat_mot_646', 'feat_mot_647', 'feat_mot_648', 'feat_mot_649', 'feat_mot_650',
                  'feat_mot_651', 'feat_mot_652', 'feat_mot_653', 'feat_mot_654', 'feat_mot_655',
                  'feat_mot_656', 'feat_mot_657', 'feat_mot_658', 'feat_mot_659', 'feat_mot_660',
                  'feat_mot_661', 'feat_mot_662', 'feat_mot_663', 'feat_mot_664', 'feat_mot_665',
                  'feat_mot_666', 'feat_mot_667', 'feat_mot_668', 'feat_mot_669', 'feat_mot_670',
                  'feat_mot_671', 'feat_mot_672', 'feat_mot_673', 'feat_mot_674', 'feat_mot_675',
                  'feat_mot_676', 'feat_mot_677', 'feat_mot_678', 'feat_mot_679', 'feat_mot_680',
                  'feat_mot_681', 'feat_mot_682', 'feat_mot_683', 'feat_mot_684', 'feat_mot_685',
                  'feat_mot_686', 'feat_mot_687', 'feat_mot_688', 'feat_mot_689', 'feat_mot_690',
                  'feat_mot_691', 'feat_mot_692', 'feat_mot_693', 'feat_mot_694', 'feat_mot_695',
                  'feat_mot_696', 'feat_mot_697', 'feat_mot_698', 'feat_mot_699', 'feat_mot_700',
                  'feat_mot_701', 'feat_mot_702', 'feat_mot_703', 'feat_mot_704', 'feat_mot_705',
                  'feat_mot_706', 'feat_mot_707', 'feat_mot_708', 'feat_mot_709', 'feat_mot_710',
                  'feat_mot_711', 'feat_mot_712', 'feat_mot_713', 'feat_mot_714', 'feat_mot_715',
                  'feat_mot_716', 'feat_mot_717', 'feat_mot_718', 'feat_mot_719', 'feat_mot_720',
                  'feat_mot_721', 'feat_mot_722', 'feat_mot_723', 'feat_mot_724', 'feat_mot_725',
                  'feat_mot_726', 'feat_mot_727', 'feat_mot_728', 'feat_mot_729', 'feat_mot_730',
                  'feat_mot_731', 'feat_mot_732', 'feat_mot_733', 'feat_mot_734', 'feat_mot_735',
                  'feat_mot_736', 'feat_mot_737', 'feat_mot_738', 'feat_mot_739', 'feat_mot_740',
                  'feat_mot_741', 'feat_mot_742', 'feat_mot_743', 'feat_mot_744', 'feat_mot_745',
                  'feat_mot_746', 'feat_mot_747', 'feat_mot_748', 'feat_mot_749', 'feat_mot_750',
                  'feat_mot_751', 'feat_mot_752', 'feat_mot_753', 'feat_mot_754', 'feat_mot_755',
                  'feat_mot_756', 'feat_mot_757', 'feat_mot_758', 'feat_mot_759', 'feat_mot_760',
                  'feat_mot_761', 'feat_mot_762', 'feat_mot_763', 'feat_mot_764', 'feat_mot_765',
                  'feat_mot_766', 'feat_mot_767', 'feat_mot_768', 'feat_mot_769', 'feat_mot_770',
                  'feat_mot_771', 'feat_mot_772', 'feat_mot_773', 'feat_mot_774', 'feat_mot_775',
                  'feat_mot_776', 'feat_mot_777', 'feat_mot_778', 'feat_mot_779', 'feat_mot_780',
                  'feat_mot_781', 'feat_mot_782', 'feat_mot_783', 'feat_mot_784', 'feat_mot_785',
                  'feat_mot_786', 'feat_mot_787', 'feat_mot_788', 'feat_mot_789', 'feat_mot_790',
                  'feat_mot_791', 'feat_mot_792', 'feat_mot_793', 'feat_mot_794', 'feat_mot_795',
                  'feat_mot_796', 'feat_mot_797', 'feat_mot_798', 'feat_mot_799', 'feat_mot_800',
                  'feat_mot_801', 'feat_mot_802', 'feat_mot_803', 'feat_mot_804', 'feat_mot_805',
                  'feat_mot_806', 'feat_mot_807', 'feat_mot_808', 'feat_mot_809', 'feat_mot_810',
                  'feat_mot_811', 'feat_mot_812', 'feat_mot_813', 'feat_mot_814', 'feat_mot_815',
                  'feat_mot_816', 'feat_mot_817', 'feat_mot_818', 'feat_mot_819', 'feat_mot_820',
                  'feat_mot_821', 'feat_mot_822', 'feat_mot_823', 'feat_mot_824', 'feat_mot_825',
                  'feat_mot_826', 'feat_mot_827', 'feat_mot_828', 'feat_mot_829', 'feat_mot_830',
                  'feat_mot_831', 'feat_mot_832', 'feat_mot_833', 'feat_mot_834', 'feat_mot_835',
                  'feat_mot_836', 'feat_mot_837', 'feat_mot_838', 'feat_mot_839', 'feat_mot_840',
                  'feat_mot_841', 'feat_mot_842', 'feat_mot_843', 'feat_mot_844', 'feat_mot_845',
                  'feat_mot_846', 'feat_mot_847', 'feat_mot_848', 'feat_mot_849', 'feat_mot_850',
                  'feat_mot_851', 'feat_mot_852', 'feat_mot_853', 'feat_mot_854', 'feat_mot_855',
                  'feat_mot_856', 'feat_mot_857', 'feat_mot_858', 'feat_mot_859', 'feat_mot_860',
                  'feat_mot_861', 'feat_mot_862', 'feat_mot_863', 'feat_mot_864', 'feat_mot_865',
                  'feat_mot_866', 'feat_mot_867', 'feat_mot_868', 'feat_mot_869', 'feat_mot_870',
                  'feat_mot_871', 'feat_mot_872', 'feat_mot_873', 'feat_mot_874', 'feat_mot_875',
                  'feat_mot_876', 'feat_mot_877', 'feat_mot_878', 'feat_mot_879', 'feat_mot_880',
                  'feat_mot_881', 'feat_mot_882', 'feat_mot_883', 'feat_mot_884', 'feat_mot_885',
                  'feat_mot_886', 'feat_mot_887', 'feat_mot_888', 'feat_mot_889', 'feat_mot_890',
                  'feat_mot_891', 'feat_mot_892', 'feat_mot_893', 'feat_mot_894', 'feat_mot_895',
                  'feat_mot_896', 'feat_mot_897', 'feat_mot_898', 'feat_mot_899', 'feat_mot_900',
                  'feat_mot_901', 'feat_mot_902', 'feat_mot_903', 'feat_mot_904', 'feat_mot_905',
                  'feat_mot_906', 'feat_mot_907', 'feat_mot_908', 'feat_mot_909', 'feat_mot_910',
                  'feat_mot_911', 'feat_mot_912', 'feat_mot_913', 'feat_mot_914', 'feat_mot_915',
                  'feat_mot_916', 'feat_mot_917', 'feat_mot_918', 'feat_mot_919', 'feat_mot_920',
                  'feat_mot_921', 'feat_mot_922', 'feat_mot_923', 'feat_mot_924', 'feat_mot_925',
                  'feat_mot_926', 'feat_mot_927', 'feat_mot_928', 'feat_mot_929', 'feat_mot_930',
                  'feat_mot_931', 'feat_mot_932', 'feat_mot_933', 'feat_mot_934', 'feat_mot_935',
                  'feat_mot_936', 'feat_mot_937', 'feat_mot_938', 'feat_mot_939', 'feat_mot_940',
                  'feat_mot_941', 'feat_mot_942', 'feat_mot_943', 'feat_mot_944', 'feat_mot_945',
                  'feat_mot_946', 'feat_mot_947', 'feat_mot_948', 'feat_mot_949', 'feat_mot_950',
                  'feat_mot_951', 'feat_mot_952', 'feat_mot_953', 'feat_mot_954', 'feat_mot_955',
                  'feat_mot_956', 'feat_mot_957', 'feat_mot_958', 'feat_mot_959', 'feat_mot_960',
                  'feat_mot_961', 'feat_mot_962', 'feat_mot_963', 'feat_mot_964', 'feat_mot_965',
                  'feat_mot_966', 'feat_mot_967', 'feat_mot_968', 'feat_mot_969', 'feat_mot_970',
                  'feat_mot_971', 'feat_mot_972', 'feat_mot_973', 'feat_mot_974', 'feat_mot_975',
                  'feat_mot_976', 'feat_mot_977', 'feat_mot_978', 'feat_mot_979', 'feat_mot_980',
                  'feat_mot_981', 'feat_mot_982', 'feat_mot_983', 'feat_mot_984', 'feat_mot_985',
                  'feat_mot_986', 'feat_mot_987', 'feat_mot_988', 'feat_mot_989', 'feat_mot_990',
                  'feat_mot_991', 'feat_mot_992', 'feat_mot_993', 'feat_mot_994', 'feat_mot_995',
                  'feat_mot_996', 'feat_mot_997', 'feat_mot_998', 'feat_mot_999', 'feat_mot_1000',
                  'feat_mot_1001', 'feat_mot_1002', 'feat_mot_1003', 'feat_mot_1004',
                  'feat_mot_1005', 'feat_mot_1006', 'feat_mot_1007', 'feat_mot_1008',
                  'feat_mot_1009', 'feat_mot_1010', 'feat_mot_1011', 'feat_mot_1012',
                  'feat_mot_1013', 'feat_mot_1014', 'feat_mot_1015', 'feat_mot_1016',
                  'feat_mot_1017', 'feat_mot_1018', 'feat_mot_1019', 'feat_mot_1020',
                  'feat_mot_1021', 'feat_mot_1022', 'feat_mot_1023', 'feat_mot_1024',
                  'feat_mot_1025', 'feat_mot_1026', 'feat_mot_1027', 'feat_mot_1028',
                  'feat_mot_1029', 'feat_mot_1030', 'feat_mot_1031', 'feat_mot_1032',
                  'feat_mot_1033', 'feat_mot_1034', 'feat_mot_1035', 'feat_mot_1036',
                  'feat_mot_1037', 'feat_mot_1038', 'feat_mot_1039', 'feat_mot_1040',
                  'feat_mot_1041', 'feat_mot_1042', 'feat_mot_1043', 'feat_mot_1044',
                  'feat_mot_1045', 'feat_mot_1046', 'feat_mot_1047', 'feat_mot_1048',
                  'feat_mot_1049', 'feat_mot_1050', 'feat_mot_1051', 'feat_mot_1052',
                  'feat_mot_1053', 'feat_mot_1054', 'feat_mot_1055']

    validation_df = validation_df[cols_order]
    validation_df.fillna(0, inplace=True)

    predictions = alg_decision_tree.predict(validation_df)
    precision, recall, fscore, support = score(validation_cat, predictions, pos_label=1,
                                               average='binary')

    print(f"--- Random Tree forest ---\n"
          f"Precision: {round(precision, 3)} // Recall: {round(recall, 3)} "
          f"// Accurancy: {round((predictions == validation_cat).sum() / len(predictions), 3)}")

    predictions = alg_svm.predict(validation_df)
    precision, recall, _, _ = score(validation_cat, predictions, pos_label=1, average='binary')
    accuracy = (predictions == validation_cat).sum() / len(predictions)
    print(f"--- Support Vector machine ---\n"
          f"Precision: {round(precision, 3)} // Recall: {round(recall, 3)} "
          f"// Accurancy: {round(accuracy, 3)}")




