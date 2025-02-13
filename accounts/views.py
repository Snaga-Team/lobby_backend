from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import RegistrationSerializer, SetPasswordSerializer
from rest_framework.permissions import AllowAny


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)