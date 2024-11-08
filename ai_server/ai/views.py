import os
import sys
import subprocess
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from configure import settings


class ThreeDTryOnView(APIView):
    def post(self, request):
        # 각 이미지에 대한 키를 지정
        images = {
            "image1": request.FILES.get('image1'),  #옷
            "image2": request.FILES.get('image2')  #옷 mask
        }

        # 상대 경로 설정 (BASE_DIR을 기준으로)
        MPV3D_root = os.path.join(settings.BASE_DIR, 'M3D-VTON')

        fs = FileSystemStorage()

        try:
            for key, img in images.items():
                if img:
                    # 원하는 디렉토리에 저장 (예: cloth, cloth-mask, image)
                    if key == "image1":
                        save_path = os.path.join(MPV3D_root, 'cloth', 'SO821D03A-Q11@12=cloth_front.jpg')
                        save_path2 = os.path.join(MPV3D_root, 'cloth', 'THJ21D007-H11@10=cloth_front.jpg')
                    elif key == "image2":
                        save_path = os.path.join(MPV3D_root, 'cloth', 'SO821D03A-Q11@12=cloth_front_mask.jpg')
                        save_path2 = os.path.join(MPV3D_root, 'cloth', 'THJ21D007-H11@10=cloth_front_mask.jpg')

                    # 디렉토리 존재 여부 확인 및 생성
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    os.makedirs(os.path.dirname(save_path2), exist_ok=True)

                    fs.save(save_path, img)  # 파일을 덮어씌움
                    fs.save(save_path2, img)  # 파일을 덮어씌움
        except Exception as e:
            return JsonResponse({"error": f"이미지 저장 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 커스텀 데이터 전처리
        try:
            command = ['python', MPV3D_root + 'util/data_preprocessing.py', '--MPV3D_root',
                       MPV3D_root + '/mpv3d_example']
            data_result = subprocess.run(command, capture_output=True, text=True, check=True)
            # 실행 결과 출력
            print("스크립트 출력:")
            print(data_result.stdout)  # 표준 출력
            print("스크립트 오류:")
            print(data_result.stderr)  # 오류 출력 (있을 경우)

        except Exception as e:
            return JsonResponse({"error": f"데이터 전처리 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 각 모델 실행
        model_name = ['MTM', 'DRM', 'TFM']
        for model in model_name:
            try:
                command = ['python', MPV3D_root + '/test.py', '--model', model, '--name', model,
                           '--dataroot', MPV3D_root + '/mpv3d_example', '--datalist', 'test_pairs',
                           '--result_dir', 'results']
                model_result = subprocess.run(command, capture_output=True, text=True, check=True)
                # 실행 결과 출력
                print("스크립트 출력:")
                print(model_result.stdout)  # 표준 출력
                print("스크립트 오류:")
                print(model_result.stderr)  # 오류 출력 (있을 경우)

            except Exception as e:
                return JsonResponse({"error": model + " m실행 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # rgbd -> pcd 변환
        try:
            command = ['python', MPV3D_root + 'rgbd2pcd.py']
            rgbd_result = subprocess.run(command, capture_output=True, text=True, check=True)
            # 실행 결과 출력
            print("스크립트 출력:")
            print(rgbd_result.stdout)  # 표준 출력
            print("스크립트 오류:")
            print(rgbd_result.stderr)  # 오류 출력 (있을 경우)

        except Exception as e:
            return JsonResponse({"error": "rgbd 변환 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "파일이 성공적으로 수신되었습니다."}, status=status.HTTP_201_CREATED)