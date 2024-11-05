import os
import sys
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from configure import settings

sys.path.append(os.path.join(settings.BASE_DIR, 'M3D-VTON'))

# data_preprocessing 모듈 import
try:
    from util.data_preprocessing import preprocess_data
    from model_runner import run_model
    from rgbd2pcd import run_rgbd2pcd
except ImportError as e:
    print(f"ImportError: {e}")


class ThreeDTryOnView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request):
        # 각 이미지에 대한 키를 지정
        images = {
            "image1": request.FILES.get('image1'),
            "image2": request.FILES.get('image2'),
            "image3": request.FILES.get('image3')
        }

        # 상대 경로 설정 (BASE_DIR을 기준으로)
        MPV3D_root = os.path.join(settings.BASE_DIR, 'user-request')

        fs = FileSystemStorage()

        for key, img in images.items():
            if img:
                # 원하는 디렉토리에 저장 (예: cloth, cloth-mask, image)
                if key == "image1":
                    save_path = os.path.join(MPV3D_root, 'cloth', 'cloth_sample')
                elif key == "image2":
                    save_path = os.path.join(MPV3D_root, 'cloth-mask', 'cloth-mask_sample')
                elif key == "image3":
                    save_path = os.path.join(MPV3D_root, 'image', 'model_image')

                # 디렉토리 존재 여부 확인 및 생성
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                fs.save(save_path, img)  # 파일을 덮어씌움

        # 데이터 전처리 함수 호출
        try:
            preprocess_data(MPV3D_root)

            # 각 모델 실행 및 후속 작업
            for model_name in ['MTM', 'DRM', 'TFM']:
                run_model(model_name=model_name, dataroot=MPV3D_root, datalist='test_pairs',
                          results_dir=os.path.join(MPV3D_root, 'results'))

                # 각 모델 실행 후 run_rgbd2pcd 함수 호출
                run_rgbd2pcd(
                    depth_root=os.path.join(MPV3D_root, 'results', 'DRM', 'test_pairs', 'final-depth'),  # path to the DRM result
                    frgb_root=os.path.join(MPV3D_root, 'results', 'TFM', 'test_pairs', 'tryon'),  # path to the TFM result (front rgb)
                    parse_root=os.path.join(MPV3D_root, 'image-parse'),  # path to the parsing image
                    point_dst=os.path.join(MPV3D_root, 'results', 'aligned', 'pcd', 'test_pairs')  #path to output dir for point cloud
                )

        except Exception as e:
            return JsonResponse({"error": f"데이터 전처리 중 오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "파일이 성공적으로 수신되었습니다."}, status=status.HTTP_201_CREATED)