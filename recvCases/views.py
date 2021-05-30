import os
import zipfile
import hashlib
import logging
import json
from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from .serializers import TestCaseSerializer
from .utils import (rand_str, filter_name_list)
from .conf import ErrorMsg

logger=logging.getLogger("")
logger.setLevel(level = logging.INFO)
log_file=logging.FileHandler("recvCases/log/log.txt")
log_file.setLevel(logging.INFO)
logger.addHandler(log_file)


class UploadCases(APIView):
	
	permission_classes = [AllowAny,]

	def post(self, request):
		resp_data = {'code': 0, 'msg': 'success', 'data': {}}
		req_serializer = TestCaseSerializer(data = request.data)
		if not req_serializer.is_valid():
			resp_data['code'] = -1
			resp_data['msg'] = 'Request data error'
			return Response(data=resp_data)

		req_data = request.data
		file = req_data['file']
		zip_file = f"/tmp/{rand_str()}.zip"
		with open(zip_file, "wb") as f:
			for chunk in file:
				f.write(chunk)

		info, ret_str = self.process_zip(zip_file, req_data['problem_id'])
		os.remove(zip_file)

		if ret_str != "OK":
			resp_data['msg'] = ErrorMsg[ret_str]
			resp_data['code'] = -1
			return Response(data = resp_data)
			
		resp_data['data'] = info # info is a dict
		resp_data['data']['problem_id'] = req_data['problem_id']
		return Response(data = resp_data)


	def process_zip(self, uploaded_zip_file, problem_id, dir=""):
		try:
			zip_file = zipfile.ZipFile(uploaded_zip_file, "r")
		except zipfile.BadZipFile:
			logger.info(f'{problem_id}: The uploaded test case zip file is bad.')
			return {}, "BadZipFile"

		name_list = zip_file.namelist()
		test_case_list = filter_name_list(name_list, dir=dir)
		if not test_case_list:
			logger.info(f'{problem_id}: The uploaded test case zip file is empty.')
			return {}, "EmptyZipFile"

		test_case_id = problem_id
		test_case_dir = os.path.join(settings.TEST_CASE_DIR, test_case_id)
		try:
			os.makedirs(test_case_dir)
		except Exception as e:
			pass
		os.chmod(test_case_dir, 0o710)

		size_cache = {}
		md5_cache = {}

		# 格式化压缩包中in out文件的换行符
		# 并将文件落盘
		for item in test_case_list:
			with open(os.path.join(test_case_dir, item), "wb") as f:
				content = zip_file.read(f"{dir}{item}").replace(b"\r\n", b"\n")
				size_cache[item] = len(content)
				if item.endswith(".out"):
					md5_cache[item] = hashlib.md5(content.rstrip()).hexdigest()
				f.write(content)

		# 保留了spj字段 为了兼容judge server
		# 不提供spj测试用例的上传
		test_case_info = {"spj": False, "test_cases": {}}

		info = {}

		# ["1.in", "1.out", "2.in", "2.out"] => [("1.in", "1.out"), ("2.in", "2.out")]
		test_case_list = zip(*[test_case_list[i::2] for i in range(2)])
		# 有多少组用例，下面的循环执行几次
		for index, item in enumerate(test_case_list):
			data = {"stripped_output_md5": md5_cache[item[1]],
					"input_size": size_cache[item[0]],
					"output_size": size_cache[item[1]],
					"input_name": item[0],
					"output_name": item[1]}
			info[str(index + 1)] = data
			test_case_info["test_cases"][str(index + 1)] = data

		# 写入测试用例的info文件
		with open(os.path.join(test_case_dir, "info"), "w", encoding="utf-8") as f:
			f.write(json.dumps(test_case_info, indent=4))

		# 更改in out info文件的权限
		for item in os.listdir(test_case_dir):
			os.chmod(os.path.join(test_case_dir, item), 0o640)
		logger.info(f'{problem_id}: Test cases upload success.')
		return info, "OK"