from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_service import analyse_query
from .models import CustomerQuery
from .serializers import CustomerQuerySerializer, StatusUpdateSerializer


class QueryListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerQuerySerializer

    @extend_schema(parameters=[
        OpenApiParameter('search', str, description='Search by customer name or email'),
        OpenApiParameter('category', str, enum=['Technical', 'Billing', 'General', 'Account Related']),
        OpenApiParameter('priority', str, enum=['Low', 'Medium', 'High']),
        OpenApiParameter('status', str, enum=['Pending', 'In Progress', 'Resolved']),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = CustomerQuery.objects.filter(created_by=self.request.user)

        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        priority = self.request.query_params.get('priority')
        query_status = self.request.query_params.get('status')

        if search:
            queryset = queryset.filter(Q(customer_name__icontains=search) | Q(email__icontains=search))
        if category:
            queryset = queryset.filter(category__iexact=category)
        if priority:
            queryset = queryset.filter(priority__iexact=priority)
        if query_status:
            queryset = queryset.filter(status__iexact=query_status)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QueryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerQuerySerializer

    def get_queryset(self):
        # user can only access their own queries, others will give 404
        return CustomerQuery.objects.filter(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        query = self.get_object()
        query.delete()
        return Response({'message': 'Query deleted successfully'}, status=status.HTTP_200_OK)


class QueryStatusUpdateView(APIView):

    @extend_schema(request=StatusUpdateSerializer, responses=CustomerQuerySerializer)
    def patch(self, request, pk):
        query = get_object_or_404(CustomerQuery, pk=pk, created_by=request.user)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query.status = serializer.validated_data['status']
        query.save()
        return Response(CustomerQuerySerializer(query).data)


class QueryAnalyzeView(APIView):

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def post(self, request, pk):
        query = get_object_or_404(CustomerQuery, pk=pk, created_by=request.user)

        result = analyse_query(query.subject, query.description)

        query.category = result['category']
        query.priority = result['priority']
        query.suggested_response = result['suggested_response']
        query.analysed_by = result['source']
        query.analysed_at = timezone.now()
        query.save()

        return Response({
            'message': 'Query analysed successfully',
            'ai_used': result['source'],
            'analysis': {
                'category': result['category'],
                'priority': result['priority'],
                'suggested_response': result['suggested_response'],
            },
            'query': CustomerQuerySerializer(query).data,
        })


class DashboardView(APIView):

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        queries = CustomerQuery.objects.filter(created_by=request.user)

        data = {
            'total': queries.count(),
            'pending': queries.filter(status='Pending').count(),
            'in_progress': queries.filter(status='In Progress').count(),
            'resolved': queries.filter(status='Resolved').count(),
            'high_priority': queries.filter(priority='High').count(),
        }
        return Response(data)
