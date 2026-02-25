# api_views/base.py

"""
Base classes, mixins, and utilities for all API views.
This module provides the foundation for all domain-specific views.
"""

from rest_framework import viewsets, status, generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from django.db import models, transaction
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

# Set up logger
logger = logging.getLogger(__name__)


# ============================================================
# BASE VIEWSET
# ============================================================

class BaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all LMS API endpoints.
    Provides common functionality:
    - Authentication defaults
    - Permission handling
    - Error logging
    - Query optimization
    - Response formatting
    """
    
    # Default authentication classes
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    
    # Default permission - require authentication
    permission_classes = [IsAuthenticated]
    
    # Default pagination class (will be set in settings)
    pagination_class = None
    
    # Default lookup field
    lookup_field = 'pk'
    
    # Whether to include soft-deleted items
    include_deleted = False
    
    def get_authenticators(self):
        """Get list of authenticators."""
        return [auth() for auth in self.authentication_classes]
    
    def get_permissions(self):
        """
        Get list of permissions for the current action.
        Override this to set action-specific permissions.
        """
        return [perm() for perm in self.permission_classes]
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer.
        Includes request and user for all serializers.
        """
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'user': self.request.user if self.request else None,
            'view': self,
        })
        return context
    
    def get_queryset(self):
        """
        Get the base queryset with optimizations.
        Override in child classes to add prefetch/select_related.
        """
        queryset = super().get_queryset()
        
        # Filter out deleted items unless explicitly requested
        if not self.include_deleted and hasattr(queryset.model, 'deleted_at'):
            queryset = queryset.filter(deleted_at__isnull=True)
        
        return queryset
    
    def handle_exception(self, exc):
        """
        Handle exceptions with proper logging.
        Returns appropriate error response.
        """
        # Log the exception
        logger.error(
            f"Exception in {self.__class__.__name__}: {str(exc)}",
            exc_info=True,
            extra={
                'user': self.request.user.id if self.request.user else None,
                'path': self.request.path if self.request else None,
                'method': self.request.method if self.request else None,
            }
        )
        
        # Handle known exceptions
        if isinstance(exc, (PermissionDenied, ValidationError, NotFound)):
            return super().handle_exception(exc)
        
        # Handle all others with generic message
        return Response(
            {
                'error': 'An unexpected error occurred',
                'detail': str(exc) if settings.DEBUG else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Generic stats endpoint.
        Override in child classes to provide domain-specific statistics.
        """
        return Response({
            'message': 'Stats endpoint not implemented',
            'domain': self.__class__.__name__
        })


# ============================================================
# READ-ONLY VIEWSET
# ============================================================

class ReadOnlyViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    ViewSet that provides only read operations (GET).
    Useful for content delivery endpoints.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'user': self.request.user if self.request else None,
        })
        return context


# ============================================================
# PRACTICE VIEWSET
# ============================================================

class PracticeViewSet(BaseViewSet):
    """
    Base ViewSet for practice attempt endpoints.
    Provides common functionality for all practice domains.
    """
    
    # Practice-specific permissions
    permission_classes = [IsAuthenticated]
    
    # Maximum attempts per cycle
    max_attempts_per_cycle = 3
    
    def get_queryset(self):
        """Filter queryset to current user by default."""
        queryset = super().get_queryset()
        
        # If model has user field, filter by current user
        if hasattr(queryset.model, 'user'):
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def get_current_cycle_info(self, user, focus):
        """
        Get current cycle and attempt number for a focus.
        Returns dict with cycle_number and attempt_number.
        """
        model = self.get_queryset().model
        
        # Get latest attempt
        latest = model.objects.filter(
            user=user,
            focus=focus
        ).order_by('-cycle_number', '-attempt_number').first()
        
        if not latest:
            # First attempt ever
            return {
                'cycle_number': 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        # Check if passed based on model fields
        is_passed = False
        if hasattr(latest, 'is_passed'):
            is_passed = latest.is_passed
        elif hasattr(latest, 'is_mastered'):
            is_passed = latest.is_mastered
        
        if is_passed:
            # Already passed in this cycle - start new cycle
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        if latest.attempt_number >= self.max_attempts_per_cycle:
            # Used all attempts in current cycle - new cycle
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        # Continue current cycle
        remaining = self.max_attempts_per_cycle - latest.attempt_number
        return {
            'cycle_number': latest.cycle_number,
            'attempt_number': latest.attempt_number + 1,
            'attempts_remaining': remaining - 1
        }
    
    def validate_attempt_allowed(self, user, focus):
        """
        Validate that user is allowed to make another attempt.
        Raises ValidationError if not allowed.
        """
        info = self.get_current_cycle_info(user, focus)
        
        if info['attempts_remaining'] < 0:
            raise ValidationError(
                f"No attempts remaining in current cycle. "
                f"Maximum {self.max_attempts_per_cycle} attempts allowed."
            )
        
        return info
    
    @transaction.atomic
    def create_attempt(self, request, focus, answers_data, **kwargs):
        """
        Create a new practice attempt.
        To be implemented by child classes.
        """
        raise NotImplementedError("Child classes must implement create_attempt")
    
    def create(self, request, *args, **kwargs):
        """
        Create a new practice attempt.
        Validates attempt count and creates the attempt.
        """
        try:
            # Validate request data
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Get focus from validated data
            focus_id = serializer.validated_data.get('focus_id')
            
            # Check if user can attempt
            info = self.validate_attempt_allowed(request.user, focus_id)
            
            # Create the attempt
            attempt = self.create_attempt(
                request=request,
                focus=focus_id,
                answers_data=serializer.validated_data.get('answers', []),
                cycle_number=info['cycle_number'],
                attempt_number=info['attempt_number'],
                **serializer.validated_data
            )
            
            # Return success response
            return Response({
                'success': True,
                'attempt_id': attempt.id,
                'score': attempt.score_percent if hasattr(attempt, 'score_percent') else None,
                'passed': attempt.is_passed if hasattr(attempt, 'is_passed') else None,
                'cycle_number': info['cycle_number'],
                'attempt_number': info['attempt_number'],
                'attempts_remaining': info['attempts_remaining'],
                'message': 'Practice attempt recorded successfully'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except NotImplementedError:
            return Response({
                'success': False,
                'error': 'Practice attempt creation not implemented for this domain'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        except Exception as e:
            logger.error(f"Practice attempt failed: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Failed to record practice attempt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# TEST VIEWSET
# ============================================================

class TestViewSet(BaseViewSet):
    """
    Base ViewSet for test attempt endpoints.
    Provides common functionality for all test domains.
    """
    
    permission_classes = [IsAuthenticated]
    max_attempts_per_cycle = 3
    
    def get_queryset(self):
        """Filter queryset to current user by default."""
        queryset = super().get_queryset()
        
        if hasattr(queryset.model, 'user'):
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def get_current_cycle_info(self, user, focus=None, task=None, unit=None):
        """
        Get current cycle and attempt number for a test.
        Handles different test types (focus, task, unit).
        """
        model = self.get_queryset().model
        
        # Build filter based on what's provided
        filter_kwargs = {'user': user}
        if focus:
            filter_kwargs['focus'] = focus
        if task:
            filter_kwargs['task'] = task
        if unit:
            filter_kwargs['unit'] = unit
        
        # Get latest attempt
        latest = model.objects.filter(**filter_kwargs).order_by(
            '-cycle_number', '-attempt_number'
        ).first()
        
        if not latest:
            return {
                'cycle_number': 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        # Check if mastered
        is_mastered = False
        if hasattr(latest, 'is_mastered'):
            is_mastered = latest.is_mastered
        elif hasattr(latest, 'is_passed'):
            is_mastered = latest.is_passed
        
        if is_mastered:
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle,
                'mastered': True
            }
        
        if latest.attempt_number >= self.max_attempts_per_cycle:
            return {
                'cycle_number': latest.cycle_number + 1,
                'attempt_number': 1,
                'attempts_remaining': self.max_attempts_per_cycle
            }
        
        remaining = self.max_attempts_per_cycle - latest.attempt_number
        return {
            'cycle_number': latest.cycle_number,
            'attempt_number': latest.attempt_number + 1,
            'attempts_remaining': remaining - 1
        }
    
    def validate_test_allowed(self, user, focus=None, task=None, unit=None):
        """
        Validate that user is allowed to take another test.
        """
        info = self.get_current_cycle_info(user, focus, task, unit)
        
        if info.get('mastered'):
            raise ValidationError("This item is already mastered.")
        
        if info['attempts_remaining'] < 0:
            raise ValidationError(
                f"No attempts remaining in current cycle. "
                f"Maximum {self.max_attempts_per_cycle} attempts allowed."
            )
        
        return info
    
    @transaction.atomic
    def create_test_attempt(self, request, **kwargs):
        """Create a new test attempt. Implement in child classes."""
        raise NotImplementedError("Child classes must implement create_test_attempt")
    
    def create(self, request, *args, **kwargs):
        """Create a new test attempt."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Extract test-specific fields
            focus_id = serializer.validated_data.get('focus_id')
            task_id = serializer.validated_data.get('task_id')
            unit_id = serializer.validated_data.get('unit_id')
            session_id = serializer.validated_data.get('session_id')
            
            # Validate attempt allowed
            info = self.validate_test_allowed(
                request.user,
                focus=focus_id,
                task=task_id,
                unit=unit_id
            )
            
            # Create the test attempt
            attempt = self.create_test_attempt(
                request=request,
                cycle_number=info['cycle_number'],
                attempt_number=info['attempt_number'],
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'attempt_id': attempt.id,
                'score': attempt.score_percent if hasattr(attempt, 'score_percent') else attempt.overall_score if hasattr(attempt, 'overall_score') else None,
                'mastered': attempt.is_mastered if hasattr(attempt, 'is_mastered') else attempt.is_passed if hasattr(attempt, 'is_passed') else None,
                'cycle_number': info['cycle_number'],
                'attempt_number': info['attempt_number'],
                'attempts_remaining': info['attempts_remaining'],
                'message': 'Test attempt recorded successfully'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except NotImplementedError:
            return Response({
                'success': False,
                'error': 'Test attempt creation not implemented for this domain'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        except Exception as e:
            logger.error(f"Test attempt failed: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Failed to record test attempt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# PROGRESS VIEWSET
# ============================================================

class ProgressViewSet(BaseViewSet):
    """
    Base ViewSet for progress/dashboard endpoints.
    Provides common progress calculation utilities.
    """
    
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']  # Read-only
    
    def get_user_progress(self, user):
        """
        Get progress data for a user.
        To be implemented by child classes.
        """
        raise NotImplementedError("Child classes must implement get_user_progress")
    
    def list(self, request, *args, **kwargs):
        """Get progress overview."""
        try:
            progress = self.get_user_progress(request.user)
            serializer = self.get_serializer(progress)
            return Response(serializer.data)
        except NotImplementedError:
            return Response({
                'error': 'Progress tracking not implemented for this domain'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as e:
            logger.error(f"Progress retrieval failed: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to retrieve progress data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get quick progress summary."""
        # Override in child classes for lightweight summary
        return Response({
            'message': 'Summary endpoint not implemented'
        })


# ============================================================
# MIXINS
# ============================================================

class UserFilterMixin:
    """
    Mixin to automatically filter queryset by current user.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'user'):
            return queryset.filter(user=self.request.user)
        return queryset


class MultipleFieldLookupMixin:
    """
    Mixin to allow lookup by multiple fields (e.g., slug, number).
    """
    lookup_fields = ['pk']  # Default lookup fields
    
    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter_kwargs = {}
        
        for field in self.lookup_fields:
            if self.kwargs.get(field):
                filter_kwargs[field] = self.kwargs[field]
        
        if not filter_kwargs:
            # Fallback to default lookup
            return super().get_object()
        
        obj = generics.get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class CachedQuerysetMixin:
    """
    Mixin to cache queryset results for performance.
    """
    
    cache_timeout = 300  # 5 minutes default
    
    def get_queryset(self):
        # Override in child classes to implement caching
        return super().get_queryset()


# ============================================================
# PERMISSIONS
# ============================================================

class IsOwnerOrReadOnly(IsAuthenticated):
    """
    Object-level permission to only allow owners to edit.
    Assumes model has a 'user' field.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsEnrolledOrReadOnly(IsAuthenticated):
    """
    Permission to only allow enrolled students to access.
    For course/content access control.
    """
    
    def has_object_permission(self, request, view, obj):
        # Implement enrollment check based on your enrollment model
        # This is a placeholder - customize based on your enrollment system
        return True


# ============================================================
# PAGINATION
# ============================================================

class StandardResultsSetPagination(viewsets.ModelViewSet.pagination_class):
    """
    Standard pagination for list endpoints.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MobileOptimizedPagination(StandardResultsSetPagination):
    """
    Smaller page size for mobile endpoints.
    """
    page_size = 10
    max_page_size = 50


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_user_activity(user, action, details=None):
    """Log user activity for analytics."""
    logger.info(
        f"User activity: {user.id} - {action}",
        extra={
            'user_id': user.id,
            'username': user.username,
            'action': action,
            'details': details,
            'timestamp': timezone.now()
        }
    )