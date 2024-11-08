import os
import sys
import subprocess
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.http import FileResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from configure import settings
import pymeshlab


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

        # PYTHONPATH 설정
        env = os.environ.copy()
        env['PYTHONPATH'] = MPV3D_root  # M3D-VTON 디렉토리 추가
        print("현재 PYTHONPATH:", env['PYTHONPATH'])  # PYTHONPATH 출력

        try:
            for key, img in images.items():
                if img:
                    # 원하는 디렉토리에 저장 (예: cloth, cloth-mask, image)
                    if key == "image1":
                        save_path = os.path.join(MPV3D_root, 'mpv3d_example', 'cloth', 'SO821D03A-Q11@12=cloth_front.jpg')
                        save_path2 = os.path.join(MPV3D_root, 'mpv3d_example', 'cloth', 'THJ21D007-H11@10=cloth_front.jpg')
                    elif key == "image2":
                        save_path = os.path.join(MPV3D_root, 'mpv3d_example','cloth-mask', 'SO821D03A-Q11@12=cloth_front_mask.jpg')
                        save_path2 = os.path.join(MPV3D_root, 'mpv3d_example', 'cloth-mask', 'THJ21D007-H11@10=cloth_front_mask.jpg')

                    # 디렉토리 존재 여부 확인 및 생성
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    os.makedirs(os.path.dirname(save_path2), exist_ok=True)
                    
                    # 기존 파일 삭제
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    if os.path.exists(save_path2):
                        os.remove(save_path2)

                    fs.save(save_path, img)  # 파일 저장
                    fs.save(save_path2, img)  # 파일 저장
        except Exception as e:
            return JsonResponse({"error": f"이미지 저장 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 커스텀 데이터 전처리
        try:
            command = ['python', os.path.join(MPV3D_root, 'util', 'data_preprocessing.py'), '--MPV3D_root',
                      os.path.join(MPV3D_root, 'mpv3d_example')]
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
                os.chdir('/home/ubuntu/grad_ai/ai_server/M3D-VTON')
                print("현재 작업 디렉토리:",os.getcwd())
                command = ['python', os.path.join(MPV3D_root, 'test.py'), '--model', model, '--name', model,
                           '--dataroot', os.path.join(MPV3D_root, 'mpv3d_example'), '--datalist', 'test_pairs',
                           '--results_dir', os.path.join(MPV3D_root, 'results')]
                model_result = subprocess.run(command, capture_output=True, text=True, check=True)
                # 실행 결과 출력
                print("스크립트 출력:")
                print(model_result.stdout)  # 표준 출력
                print("스크립트 오류:")
                print(model_result.stderr)  # 오류 출력 (있을 경우)

            except Exception as e:
                return JsonResponse({"error": f"{model} 실행 중 오류 발생: {e.stderr}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # rgbd -> pcd 변환
        try:
            command = ['python', os.path.join(MPV3D_root, 'rgbd2pcd.py')]
            rgbd_result = subprocess.run(command, capture_output=True, text=True, check=True)
            # 실행 결과 출력
            print("스크립트 출력:")
            print(rgbd_result.stdout)  # 표준 출력
            print("스크립트 오류:")
            print(rgbd_result.stderr)  # 오류 출력 (있을 경우)

        except Exception as e:
            return JsonResponse({"error": "rgbd 변환 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ply 파일 경로 설정
        ply_file_path = os.path.join(MPV3D_root, 'results', 'aligned','pcd', 'test_pairs', 'BJ721E05W-J11@9=person.ply')
        
        # ply 불러오기
        try:
            ms = pymeshlab.MeshSet()
            ms.load_new_mesh(ply_file_path)
        except Exception as e:
            return JsonResponse({"error": f"ply 탐색 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        #Normal Estimation
        try:
            ms.apply_filter('compute_normal_for_point_clouds')
        except Exception as e:
            return JsonResponse({"error": f"normal estimation 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        #Poisson mesh 하기
        try:
            ms.apply_filter('generate_surface_reconstruction_screened_poisson', depth=9)
            output_path = os.path.join(MPV3D_root, 'results', 'output.obj')
            ms.save_current_mesh(output_path)
        except Exception as e:
            return JsonResponse({"error": f"메쉬 처리 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       #output.obj 파일 전송
        try:
            response = FileResponse(open(output_path, 'rb'), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_path)}"'
            return response
        
        except Exception as e:
            return JsonResponse({"error": f"파일 전송 중 오류 발생: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
