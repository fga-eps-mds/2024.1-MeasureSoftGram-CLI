# import subprocess


# def capture(command):
#     proc = subprocess.Popen(
#         command,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#     )
#     out, err = proc.communicate()
#     return out, err, proc.returncode


# def test_change_name_return_code_invalid():
#     out, _, returncode = capture(
#         ["measuresoftgram", "change-name", "81357858", "new name"]
#     )

#     assert returncode == 1
