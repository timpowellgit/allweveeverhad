import sys
import pickle
import mido
from collections import defaultdict, OrderedDict
from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
import math
import json
from models import db, Artwork, Image
import os
from tqdm import tqdm
import numpy as np
import re
from collections import Counter, OrderedDict

# ---

# ACCEPT_ONLY_IMAGE_ID_MIN = 1250205
# ACCEPT_ONLY_IMAGE_ID_MAX = 1250742

# TRACK_SCORE_OF_IMAGE_IDS = [
#   [1250580],
#   [1250574],
# ]

# ---

IMG_BLACKLIST = [800175, 435716, 81573, 762831, 177194, 499334, 730007, 700771, 335367, 383716, 198935, 547409, 78209, 1102175, 1102055, 569218, 1102060, 210786, 668866, 91049, 711509, 91799, 520968, 550537, 1235756, 378077, 208735, 290389, 498755, 428709, 657348, 157413, 1203175, 779539, 1212921, 437749, 385213, 612309, 1133285, 136809, 714106, 74526, 226663, 729699, 194982, 370264, 600860, 512278, 269703, 31795, 1210490, 601226, 1211217, 429304, 387397, 448348, 677161, 288055, 737962, 441157, 755243, 122196, 801931, 1235744, 700757, 609525, 31265, 132219, 31654, 1203174, 732589, 355192, 453701, 796251, 108392, 228858, 178875, 225696, 607865, 29717, 250795, 299448, 738740, 346461, 121358, 230098, 581426, 652895, 475798, 9466, 43704, 784880, 1210482, 586675, 1211184, 300083, 728213, 264624, 597450, 464023, 454599, 206397, 55127, 1218637, 1226088, 636828, 423756, 716345, 438100, 463856, 741197, 426106, 797227, 250551, 37303, 190370, 363790, 134655, 598134, 628163, 716698, 88700, 252500, 538128, 151768, 626342, 329492, 90218, 66980, 479742, 213735, 306819, 314704, 518715, 63839, 201514, 75976, 247837, 1218856, 361506, 786305, 161553, 557752, 600266, 205973, 33941, 1221578, 118449, 243484, 462177, 280443, 604971, 73026, 829535, 605624, 1220832, 198935, 547409, 1102060, 1102055, 1102175, 177194, 78209, 383716, 435716, 730007, 1102055, 1102175, 1102060, 499334, 198935, 547409, 668866, 520968, 800175, 91799, 335367, 1235756, 569218, 498755, 378077, 208735, 210786, 74526, 700771, 428709, 157413, 762831, 612309, 385213, 290389, 1133285, 194982, 609525, 512278, 600860, 91049, 801931, 31795, 550537, 711509, 250795, 714106, 108392, 370264, 136809, 1203175, 355192, 9466, 1210490, 737962, 1212921, 738740, 387397, 610132, 755243, 729699, 1210482, 601226, 230098, 475798, 448348, 784880, 437749, 426106, 1221578, 1226088, 226663, 1211184, 311732, 429304, 269703, 103151, 716698, 438100, 441157, 1211217, 732589, 700757, 754376, 122196, 779539, 280443, 258933, 29717, 1218637, 31265, 657348, 206397, 1220832, 121358, 677161, 363790, 453701, 66980, 517294, 600266, 213735, 482934, 607865, 171551, 252500, 535837, 518715, 161602, 1203174, 734213, 675543, 132219, 317556, 181703, 3161, 129502, 300083, 261710, 688112, 692341, 47787, 105503, 454599, 292006, 201225, 459504, 796251, 377387, 785698, 77961, 528394, 581426, 247837, 683869, 138632, 538128, 728213, 1235744, 557752, 467066, 652895, 636828, 741197, 786305, 90218, 429913, 43704, 58266, 75976, 462177, 227846, 368674, 734598, 593784, 545750, 458098, 730608, 72237, 236934, 845636, 605624, 487608, 237490, 110405, 250551, 193265, 829535, 493895, 845641, 243484, 350305, 713766, 628163, 192673, 848596, 783269, 791123, 184315, 453729, 156516, 81942, 579323, 314704, 674352, 598134, 19114, 829534, 609517, 310270, 692159, 264624, 829536, 721648, 88700, 73026, 423756, 549505, 351473, 18455, 225696, 694224, 33941, 559950, 793237, 276206, 586675, 718784, 227916, 168542, 215020, 548193, 859409, 601316, 573496, 264920, 164356, 676715, 86490, 355568, 280859, 421764, 634644, 541435, 31654, 264287, 359281, 361506, 609499, 39446, 92922, 315915, 270510, 797227, 21018, 557203, 63839, 343139, 463856, 190370, 466113, 729299, 290674, 1218856, 211070, 737359, 88783, 570113, 306819, 540986, 1244655, 433040, 666597, 464023, 429180, 812350, 545024, 401210, 732156, 177926, 329492, 604971, 205973, 286065, 285463, 118449, 460022, 574038, 7665, 76158, 72847, 334379, 853013, 770088, 266049, 30200, 408410, 737671, 123417, 111245, 560919, 55127, 638704, 638372, 626342, 166641, 716882, 170108, 1216359, 1245499, 137335, 378527, 266607, 552684, 654316, 479742, 460505, 273672, 346461, 742337, 166333, 348791, 151768, 220866, 68767, 388346, 247038, 6733, 573511, 1207854, 770148, 716345, 397565, 673914, 514692, 362651, 488433, 363090, 314689, 1087394, 586619, 688395, 248364, 1234102, 390472, 7653, 347097, 132817, 387854, 34553, 669904, 93874, 780629, 128454, 251416, 101318, 191393, 152240, 69673, 445933, 154021, 185801, 726338, 371552, 597450, 103658, 659372, 299448, 389621, 349212, 322040, 358221, 781756, 565890, 277895, 1226339, 395144, 80220, 199748, 102468, 123307, 564869, 621499, 735570, 78752, 163268, 255910, 649075, 513800, 750118, 488006, 601836, 150106, 188211, 524072, 594230, 1030731, 21515, 420761, 666082, 282836, 736960, 215578, 161553, 162562, 361163, 473095, 348277, 64126, 155050, 327091, 248890, 523667, 531002, 316027, 704952, 358293, 408046, 338100, 531047, 459148, 822676, 653340, 495213, 194311, 604145, 1145926, 424194, 354132, 419003, 448372, 311266, 1234262, 394887, 281669, 758700, 647290, 35047, 230916, 501697, 343094, 768719, 306320, 588010, 512431, 607687, 126513, 693635, 818444, 150700, 773567, 816668, 555010, 533970, 135536, 416849, 170188, 187566, 752947, 304893, 658967, 736072, 1041810, 720064, 452799, 508413, 739341, 681987, 782977, 707291, 721753, 772392, 609529, 790424, 445535, 416314, 815212, 794900, 744039, 651360, 191416, 244150, 70934, 37303, 769995, 1217624, 562370, 683933, 681160, 464582, 604127, 769273, 117269, 257303, 508946, 572058, 55338, 507938, 569341, 178875, 800315, 443309, 94541, 607908, 658728, 76795, 194657, 577259, 282585, 806105, 360216, 1213525, 552506, 646310, 1235759, 645905, 592818, 307261, 763410, 449161, 299682, 203158, 35841, 694862, 810689, 52287, 758334, 40345, 472453, 403820, 423470, 100048, 486364, 215130, 382518, 719771, 291977, 581987, 516544, 295061, 1236595, 769389, 849405, 371368, 37765, 489789, 222427, 711302, 594682, 772727, 1208038, 415193, 1223352, 159656, 625528, 725556, 149559, 274910, 220671, 748605, 1200421, 320132, 234574, 810782, 185805, 528783, 592409, 320093, 306523, 229110, 279762, 49782, 517406, 161560, 326861, 853015, 201514, 574250, 651770, 27288, 540193, 961354, 648069, 628219, 624170, 692104, 822464, 559790, 102656, 13602, 147677, 146339, 742616, 472335, 20109, 116541, 1149000, 153265, 386064, 654394, 734846, 320718, 82032, 10281, 338195, 444769, 475169, 312961, 210416, 481650, 172930, 652524, 244733, 676260, 227345, 10709, 86142, 738602, 640135, 207586, 659945, 764709, 160980, 562685, 813237, 551069, 514474, 431510, 812085, 469854, 865605, 117841, 158960, 1235743, 105416, 1211219, 101026, 443986, 542797, 20909, 425555, 159339, 417494, 772815, 140196, 502847, 46863, 648457, 790487, 47937, 123477, 211202, 187568, 569911, 285400, 8810, 434970, 853009, 811195, 751320, 505401, 23850, 785636, 105311, 201036, 62220, 398569, 290045, 786947, 537180, 792649, 74263, 632443, 78514, 1065711, 784147, 182862, 14068, 473721, 82203, 469415, 773796, 134972, 520155, 331937, 761423, 447059, 454539, 156347, 792153, 90511, 643264, 707395, 541347, 649254, 767621, 648170, 60867, 781079, 139508, 491854, 94939, 626823, 326443, 562949, 138520, 480532, 476076, 516143, 1060929, 72326, 219450, 36275, 430890, 371527, 137, 550131, 320599, 497739, 498104, 288419, 406890, 795678, 412313, 550846, 59202, 305354, 773934, 667387, 588828, 178610, 260420, 131145, 576581, 548591, 623361, 486895, 425660, 155236, 66235, 729944, 236103, 1176817, 218580, 610791, 756118, 799579, 396441, 852304, 128909, 3438, 495073, 755310, 559349, 462856, 766900, 735162, 1212240, 679423, 253105, 800039, 157506, 440232, 32356, 820005, 13414, 417902, 612065, 790262, 772223, 407911, 479707, 671333, 772032, 477097, 691490, 56809, 151813, 441609, 534415, 171748, 1235746, 24813, 349130, 377666, 785233, 279686, 711119, 97621, 735280, 491156, 452840, 488805, 540682, 107091, 961251, 190452, 619802, 678326, 639635, 1211180, 479600, 1224879, 130932, 638698, 136737, 277539, 690442, 557038, 303742, 140487, 8852, 206630, 370463, 701931, 603733, 715762, 1065635, 165613, 84847, 469831, 450988, 637182, 142152, 178849, 790728, 275688, 806806, 455679, 283075, 479711, 605292, 94817, 410892, 707054, 741862, 279940, 575570, 79888, 191574, 461076, 133972, 288055, 723746, 202843, 166864, 58154, 3153, 228005, 124042, 368449, 342262, 629672, 275006, 597558, 460278, 417585, 844, 477676, 667986, 717282, 389382, 370669, 849389, 809470, 258949, 429851, 1219754, 588064, 786837, 649406, 626507, 297164, 99663, 373379, 439195, 691560, 174415, 588749, 268252, 652863, 421039, 328307, 852918, 495242, 868568, 103506, 458401, 34890, 568644, 729491, 655670, 424591, 497960, 81573, 799166, 386767, 399269, 373355, 32908, 246852, 53057, 205276, 449295, 344135, 308854, 72826, 675759, 782831, 670061, 195507, 457945, 186134, 11621, 506621, 320894, 238055, 852919, 534620, 576348, 420376, 577353, 321329, 859411, 104930, 804651, 83093, 376835, 188749, 716858, 807814, 681723, 132049, 743081, 384806, 750697, 488364, 859101, 163782, 138730, 207897, 334444, 712550, 16262, 1235762, 159323, 595148, 257164, 449465, 389061, 219248, 449286, 731124, 498168, 234771, 358863, 375454, 813183, 535409, 241077, 465194, 21261, 523465, 454629, 277500, 364692, 617763, 808016, 290777, 101161, 788017, 45657, 467801, 512486, 142609, 475650, 312747, 591622, 161407, 13357, 458570, 438548, 780601, 116484, 271139, 211270, 636000, 1046393, 536428, 120892, 263521, 191568, 647445, 491329, 565361, 464074, 962863, 457569, 874789, 263220, 136554, 398989, 593991, 407449, 323440, 237301, 735746, 1235760, 641070, 447450, 498647, 423095, 803200, 773986, 445125, 539025, 94910, 494062, 682866, 554354, 222630, 325006, 666795, 815490, 771466, 27713, 36136, 30842, 770818, 477935, 42770, 721117, 671530, 504764, 225706, 230317, 576959, 62317, 29344, 541103, 141250, 1060300, 109095, 669435, 321454, 146847, 579493, 355519, 106338, 701037, 365649, 874895, 852306, 403576, 360863, 65382, 356268, 500142, 853016, 302072, 1235761, 776613, 13437, 243509, 50665, 225266, 39036, 961456, 384485, 17509, 756802, 276556, 480153, 186480, 616821, 759147, 549482, 785310, 336033, 241032, 143707, 272139, 528439, 163456, 730721, 514588, 233585, 859410, 638616, 198456, 128737, 228989, 960690, 247996, 78744, 709927, 698197, 55592, 222175, 470728, 210213, 327685, 725813, 178283, 176775, 470507, 490314, 75904, 463648, 228632, 569720, 71024, 740606, 775484, 771182, 309805, 64682, 5850, 194145, 425229, 735052, 406932, 486824, 257640, 755528, 36256, 417745, 799016, 1211857, 601139, 607309, 640538, 491807, 751625, 450893, 514949, 815407, 73237, 167836, 356337, 301621, 85707, 439338, 97929, 670503, 853817, 169915, 775424, 185295, 227618, 110227, 678409, 614299, 501569, 479844, 1045883, 399530, 184396, 381126, 790144, 382001, 36103, 374537, 868506, 87147, 208477, 692302, 47597, 726867, 415372, 962780, 723989, 11676, 236267, 338065, 772309, 398131, 371342, 252053, 227092, 622868, 429825, 452428, 43483, 665125, 467741, 72119, 206478, 25709, 55180, 731727, 28880, 740842, 105729, 1239706, 791040, 754255, 748221, 442911, 569732, 509993, 741288, 457454, 800237, 464330, 144498, 161007, 1096814, 438358, 771593, 414707, 726569, 152930, 767671, 238353, 230121, 211249, 581399, 190162, 356137, 797331, 464669, 26413, 367622, 287705, 620306, 318042, 62984, 617032, 532641, 769182, 312399, 788110, 56651, 568337, 25708, 798998, 426821, 460424, 733074, 403900, 251316, 711074, 452717, 753904, 678373, 799094, 714921, 192031, 636745, 389147, 670752, 322312, 486437, 182759, 808285, 396233, 279476, 145658, 98021, 276571, 61606, 715738, 47355, 532526, 467888, 962689, 44681, 77497, 83663, 963110, 103476, 773371, 603262, 507391, 110581, 409889, 146034, 514052, 240505, 71930, 627610, 242212, 624950, 785172, 319619, 564908, 700404, 289727, 745593, 145381, 614428, 444985, 448200, 32709, 715200, 700660, 252541, 261414, 416839, 711822, 92420, 395712, 414987, 59308, 195001, 809555, 853008, 351236, 1046732, 669696, 742584, 50339, 817354, 808881, 634116, 329372, 73005, 329876, 440589, 438082, 423554, 198935, 547409, 1102060, 1102175, 1102055]

# ---

DIFF_PICKLE_FILES_DIR_PATH = os.environ['DIFF_PICKLE_FILES_DIR_PATH']
LAST_WEIGHTS = os.environ['LAST_WEIGHTS']
#DIFF_PICKLE_FILES_DIR_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/realtime-multi-pickles'
# DIFF_PICKLE_FILES_DIR_PATH = '/Volumes/Phatty/ART-freeriots-to-make-more-room-on-tw/realtime-multi-pickles post tf join backup final weights apr 16 BKP'
ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']

# ---

MAX_ITEMS_TO_SEND_BACK = 50

MIDI_CHANNEL = 3
MIDI_CONTROL_TO_ALGO = {
  13: 'image_ratio',
  14: 'multi_hist',
  15: 'lines_angle_hist',
  16: 'lines_vert_dist_hist',
  17: 'lines_horiz_dist_hist',

  31: 'hist_ahash',
  32: 'hist_dhash',
  33: 'hist_phash',
  34: 'hist_whash',

  49: 'tf',
  50: 'hist',
  51: 'ahash',
  52: 'dhash',
  53: 'phash',
  54: 'whash',
}
ALGOS = MIDI_CONTROL_TO_ALGO.values()

NORMALIZATION = {
  # max euclidean distance to 2048 dimensions
  'tf': math.sqrt(2048),
  # unsure of current normalization, but values are small enough
  'hist': 1,
  'ahash': 64,   
  'dhash': 64,
  'phash': 64,
  'whash': 64,
  'hist_ahash': 1,
  'hist_dhash': 1,
  'hist_phash': 1,
  'hist_whash': 1,

  'image_ratio': 1,
  'multi_hist': 1,
  'lines_angle_hist': 64,
  'lines_vert_dist_hist': 64,
  'lines_horiz_dist_hist': 64,
}
# key is algo, value is multiplier
KNOB_MULTIPLIER = defaultdict(lambda:1)

# 0.0 - 1.0 divided into as many intervals as there are faders
FADER_INTERPOLATION_X = [1.0/7*i for i in range(8)]
# default is linear interpolation -- i.e. x=y
FADER_INTERPOLATION_Y = FADER_INTERPOLATION_X[:]
FADER_CHANNEL_MIN = 77
FADER_CHANNEL_MAX = 84

# ---

db.init(ARTWORKS_SQLITE_PATH)

# ---

# inport = mido.open_input()

# ---

# OK TO SET DEFAULTS HERE
# all_weights = defaultdict(int)
# global_transfer_value = 1
# global_input_max = 100.0
# global_output_max = 100.0


# values set on apr 16

global_output_max = global_input_max = global_transfer_value = all_weights = None



# / DEFAULTS

def image_obj_to_url(img_obj):
  source_name = img_obj.artwork_id.source_name
  key = None

  URL_PREFIX = 'http://67.205.174.228:48809/2fee9d62-66cf-4ae3-af4c-e3b2a1f1b32e/'

  if source_name == 'artsy':
    key = '/'.join(img_obj.img_local_path.split('/')[-2:])
    url = URL_PREFIX + 'artsy/{}'.format(key)
  elif source_name == 'met':
    key = '/'.join(img_obj.img_local_path.split('/')[-3:])
    url = URL_PREFIX + 'met/{}'.format(key)
  elif source_name == 'allpainters':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'allpainters/{}'.format(key)
  elif source_name == 'moma':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    # remove ?sha= portion as a question mark
    # in the filename wasn't working well
    key = re.sub(r'\.jpg\?.+', '.jpg', key)
    url = URL_PREFIX + 'moma/{}'.format(key)
  elif source_name == 'jflauda':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'jflauda/{}'.format(key)
  elif source_name == 'guidomolinari':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'guidomolinari/{}'.format(key)
  elif source_name == 'adam_email_apr18':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'adam_email_apr18/{}'.format(key)
  elif source_name == 'tate':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'tate/{}'.format(key)
  elif source_name == 'rijksmuseum':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'rijksmuseum/{}'.format(key)
  elif source_name == 'pompidou':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'pompidou/{}'.format(key)
  elif source_name == 'museoreinasofia':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'museoreinasofia/{}'.format(key) 
  elif source_name == 'imagesdart':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'imagesdart/{}'.format(key)
  elif source_name == 'guggenheim':
    key = '/'.join(img_obj.img_local_path.split('/')[-1:])
    url = URL_PREFIX + 'guggenheim/{}'.format(key) 
  
  return url

def image_id_artwork_info(img_id):
  img_db_obj = Image.get_by_id_safe(img_id)
  if img_db_obj:
    img_artwork = img_db_obj.artwork_id
    s = u'{} - {}'.format(img_artwork.artist, img_artwork.title)
    return s

def reset_values():
  global global_transfer_value,global_input_max,global_output_max, all_weights, MAX_ITEMS_TO_SEND_BACK
  global_transfer_value = 2.8346456692913384
  global_input_max = 77.953
  global_output_max = 1.299
  MAX_ITEMS_TO_SEND_BACK = 50
  all_weights = defaultdict(int)
  all_weights.update({"ahash":0.787,"dhash":1.102,"hist":17.008,"hist_ahash":0.630,
    "hist_dhash":0.630,"hist_phash":12.441,"hist_whash":0.945,"image_ratio":1.102,
    "lines_angle_hist":5.512,"lines_horiz_dist_hist":3.622,"lines_vert_dist_hist":3.622,
    "multi_hist":6.772,"phash":3.150,"tf":20.000,"whash":0.787})

def set_last_weights():
  global global_transfer_value,global_input_max,global_output_max, all_weights

  if os.path.isfile(os.path.join(LAST_WEIGHTS, 'pickle_weights.pickle')):
    # Store configuration file values
    print 'using most recent weights'
    pickle_filepath = os.path.join(LAST_WEIGHTS, 'pickle_weights.pickle')
    with open(pickle_filepath) as f:
      pickle_data = pickle.load(f)
      global_transfer_value = pickle_data['global_transfer_value']
      global_input_max = pickle_data['global_input_max']
      global_output_max = pickle_data['global_output_max']
      all_weights = defaultdict(int)
      all_weights.update(pickle_data['all_weights'])
      MAX_ITEMS_TO_SEND_BACK = pickle_data['max_items']
  else:
    reset_values()


def process_calibration_message(message):
  global global_transfer_value,global_input_max,global_output_max, all_weights
  global MAX_ITEMS_TO_SEND_BACK
  global FADER_INTERPOLATION_Y
  global FADER_CHANNEL_MIN
  global FADER_CHANNEL_MAX

  # for msg in inport.iter_pending():
  #   if not (hasattr(msg, 'channel') and hasattr(msg, 'control')):
  #     continue

  #   if msg.channel != MIDI_CHANNEL:
  #     continue
  print "processing submitted values:"

  calibration = message['calibration']
  global_transfer_value = float(calibration['t_v']) #/ 127.0 * 10.0

  global_input_max = float(calibration['g_i']) #/ 127.0 * 100.0

  global_output_max = float(calibration['g_o']) #/ 127.0 * 3.0
  weights =  calibration['weights']
  for w,v in weights.iteritems():
    weights[w]=float(v)
  all_weights.update(weights)
  MAX_ITEMS_TO_SEND_BACK = int(calibration['max_items'])

  #   if FADER_CHANNEL_MAX >= msg.control >= FADER_CHANNEL_MIN:
  #     # remap fader index to list index (0-7)
  #     FADER_INTERPOLATION_Y[msg.control - FADER_CHANNEL_MIN] = msg.value / 127.0

  #   if msg.control not in MIDI_CONTROL_TO_ALGO:
  #     continue

  #   algo = MIDI_CONTROL_TO_ALGO[msg.control]
  #   # normalize fader midi value
  #   fader_val = msg.value / 127.0 * 20.0
  #   fader_val *= KNOB_MULTIPLIER[algo]
  #   all_weights[algo] = fader_val

class MyServerProtocol(WebSocketServerProtocol):
  def __init__(self, *args, **kwargs):
    self.diff_data = None
    super(MyServerProtocol, self).__init__()

  def onConnect(self, request):
    print("Client connecting: {}".format(request.peer))

    self.diff_data = []
    pickle_filepaths = os.listdir(DIFF_PICKLE_FILES_DIR_PATH)
    pickle_filepaths = filter(lambda f:f.endswith('.pickle'), pickle_filepaths)
    pickle_filepaths.sort(key=lambda _: int(os.path.splitext(_)[0].replace('file', '')))
    for pickle_filepath in tqdm(pickle_filepaths, desc='load & normalize pickle files'):
      print 'loading pickle files'
      with open(os.path.join(DIFF_PICKLE_FILES_DIR_PATH, pickle_filepath)) as f:
        pickle_data = pickle.load(f)

      # applying blacklist
      # https://stackoverflow.com/a/28256912/426790
      pickle_data = pickle_data[~pickle_data.index.isin(IMG_BLACKLIST)]

      # print 'filtering out all non-jflauda,allpainters,guidomolinari images'
      # pickle_data_index = pickle_data.index
      # selected_indices = (pickle_data_index >= ACCEPT_ONLY_IMAGE_ID_MIN) & \
      #                   (pickle_data_index <= ACCEPT_ONLY_IMAGE_ID_MAX)
      # pickle_data = pickle_data[selected_indices]

      print 'normalizing data'
      for algo, factor in NORMALIZATION.items():
        if algo not in pickle_data:
          continue
        pickle_data[algo] = 1 - (pickle_data[algo] / factor)
      self.diff_data.append(pickle_data)

      self.blacklist_indices_written = False


  def onOpen(self):
    print("WebSocket connection open.")

  def onClose(self):
    print('websocket connection closed.')
    reactor.callFromThread(reactor.stop)

  def onMessage(self, payload, isBinary):
    global global_transfer_value,global_input_max,global_output_max, all_weights
    global MAX_ITEMS_TO_SEND_BACK
    global FADER_INTERPOLATION_Y
    assert not isBinary, 'binary not supported'

    if payload == "reset":
      reset_values()  
      self.sendMessage(json.dumps({
      'weights': OrderedDict([(k, '%.3f' % all_weights[k]) for k in sorted(all_weights)]),
      'transfer_info': [(_, '%.1f' % (_/10.0) ** global_transfer_value) for _ in range(10)],
      'transfer_value': global_transfer_value,
      'global_input_max': '%.1f' % (global_input_max),
      'global_output_max': '%.1f' % (global_output_max),
      'max_items': '%d' % (MAX_ITEMS_TO_SEND_BACK)

      }))
    elif payload == "initial":
      print 'initial message'
      set_last_weights()
     
    else:
      payloadjson = json.loads(payload)
      process_calibration_message(payloadjson)

    all_img_data = []

    # track_score_of_image_ids_output = []

    for diff_img_index, diff_img in enumerate(self.diff_data):
      weighted_ids = []
      for algo in ALGOS:
        # algo can be not in the pickled diff data
        # as lines only outputs columns for horiz or vert if
        # there were vert or horiz lines found...
        if algo not in diff_img:
          continue

        # (knob * algo_diff) ** transfer
        img_algo_result = (diff_img[algo].fillna(0) ** global_transfer_value) * all_weights[algo]
        # linearly transpose all results
        img_algo_result = (img_algo_result / global_input_max) * global_output_max

        # add weighted col to output
        weighted_ids.append(img_algo_result)

      # squish weighted values
      weighted_ids = sum(weighted_ids)
      weighted_ids = weighted_ids.sort_values(ascending=False)

      # if not self.blacklist_indices_written:
      #   print 'writing blacklist'
      #   with open('/Users/greg/Desktop/blacklist pickle/{}.pickle'.format(diff_img_index), 'w') as f:
      #     pickle.dump(weighted_ids[weighted_ids>=.9].index, f)

      # for each source image, track some specific (database) image IDs
      # and print those
      # track_score_img_output = []
      # for image_id_to_track in TRACK_SCORE_OF_IMAGE_IDS[diff_img_index]:
      #   track_score_img_output.append('%.2f' % (100 * weighted_ids[image_id_to_track]))
      # track_score_of_image_ids_output.append(','.join(track_score_img_output))

      # for each image in max_items, send back values of distance per algo
      # this is displayed in the <img>'s title attribute
      winning_image_indices = weighted_ids[:MAX_ITEMS_TO_SEND_BACK].index
      winning_image_indices_algo_results = [{}] * len(winning_image_indices)
      for algo in ALGOS:
        if algo not in diff_img:
          continue

        # just the raw score please
        img_algo_result = diff_img[algo][winning_image_indices].fillna(0)
        for image_idx, winning_image_index in enumerate(winning_image_indices):
          winning_image_indices_algo_results[image_idx][algo] = img_algo_result.values[image_idx]

      # get the match score for 10 matching images (per src img)
      top_match_scores = weighted_ids[:MAX_ITEMS_TO_SEND_BACK].values
      # interpolate all match percentages (0.0 - 1.0) according to fader positions
      interpolated_top_match_scores = np.interp(top_match_scores, FADER_INTERPOLATION_X, FADER_INTERPOLATION_Y)

      # convert to percentage
      percentage_match_scores = interpolated_top_match_scores * 100.0
      # stringify matches (too long of a float will mess with table/td width output)
      percentage_match_scores = map(lambda _: '%.9f'%_, percentage_match_scores)
      image_db_objects = filter(None,map(Image.get_by_id_safe, weighted_ids[:MAX_ITEMS_TO_SEND_BACK].index))

      all_img_source_names = map(lambda obj: obj.artwork_id.source_name, image_db_objects)

      per_img_data = {
        'results': map(image_obj_to_url, image_db_objects),
        'scores': percentage_match_scores,
        'artwork_info': filter(None,map(image_id_artwork_info, weighted_ids[:MAX_ITEMS_TO_SEND_BACK].index)),
        'source_names': all_img_source_names,
        'winning_image_indices_algo_results': winning_image_indices_algo_results,
      }
      all_img_data.append(per_img_data)


    self.blacklist_indices_written = True

    # print '\t|\t'.join(track_score_of_image_ids_output)

    source_names_counter = Counter()
    for _ in all_img_data:
      source_names_counter.update(_['source_names'])

    all_img_source_names_freq_dict = dict(source_names_counter.most_common())
    all_img_source_names_freq_dict = OrderedDict([(k, all_img_source_names_freq_dict[k]) \
                                      for k in sorted(all_img_source_names_freq_dict)])
    all_img_source_names_freq_dict = str(all_img_source_names_freq_dict)

    #save weights
    pickle_filepath = 'pickle_weights.pickle'

    with open(os.path.join(LAST_WEIGHTS, pickle_filepath), 'w') as f:
      calibration = {"global_transfer_value": global_transfer_value,
      "global_input_max": global_input_max, 
      "global_output_max": global_output_max,
      "all_weights": all_weights,
      "max_items": MAX_ITEMS_TO_SEND_BACK}
      pickle.dump(calibration, f)

    # send back new results
    self.sendMessage(json.dumps({
      'imgs': all_img_data,
      'weights': OrderedDict([(k, '%.3f' % all_weights[k]) for k in sorted(all_weights)]),
      'transfer_info': [(_, '%.1f' % (_/10.0) ** global_transfer_value) for _ in range(10)],
      'transfer_value': global_transfer_value,
      'global_input_max': '%.1f' % (global_input_max),
      'global_output_max': '%.1f' % (global_output_max),
      'max_items': '%d' % (MAX_ITEMS_TO_SEND_BACK),
      'source_names_freq': all_img_source_names_freq_dict,
    }))
    return




    assert False, 'unsupported message'

  def onClose(self, wasClean, code, reason):
    print("WebSocket connection closed: {}".format(reason))

def start_server():
   log.startLogging(sys.stdout)

   factory = WebSocketServerFactory()
   factory.protocol = MyServerProtocol

   reactor.listenTCP(9000, factory)
   reactor.run()


if __name__ == '__main__':
  start_server()
