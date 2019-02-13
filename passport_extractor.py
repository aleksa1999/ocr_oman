
from Categorization import VendorExtractor
from Categorization import FuncMl
import sys
import os


if len(sys.argv) >= 2:
    src_name = sys.argv[1]
else:
    src_name = 'sample_passport/IMG_0301.jpg'

class_passport = VendorExtractor('passport')
class_func = FuncMl()

ret = class_passport.extract_MRP(src_name)
if not ret:
    # ret = class_passport.extract(src_name)
    ret = class_passport.extract(src_name, 9)

ret_parse = {}
for i in range(len(ret)):
    ret_parse[ret[i]['field_name']] = ret[i]['value']

# print json.dumps(ret_parse, indent=4)

# --------------- Save and Display Result -------------------
str_path = os.path.split(src_name)

data = [['Name', 'Value']]

for key in sorted(ret_parse.iterkeys()):
    # print "%s: %s" % (key, ret_parse[key])

    if ret_parse[key] is None:
        value = ''
    else:
        value = ret_parse[key]

    data.append([key.encode('utf8'), value.encode('utf8')])

class_func.save_csv(str_path[-1][:-4] + "_Name-value-pair.csv", data)
