from rest_framework import permissions
from api.models import OurchiveSetting, Chapter, UserBlocks, Bookmark
from django.contrib.auth.models import AnonymousUser

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:            
            return True
        return obj.user == request.user or request.user.is_superuser

class RegistrationPermitted(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        setting = OurchiveSetting.objects.filter(name='Registration Permitted').first()
        if setting.value == 'False' and request.method == 'POST':
            return False
        else:
            return True
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:   
            return True
        return obj == request.user or request.user.is_superuser

class Common:
    def user_is_blocked(owner, user):
        return UserBlocks.objects.filter(user__id=owner).filter(blocked_user__id=user).first() is not None

class UserAllowsWorkComments(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if 'chapter' in request.data:
            work = Chapter.objects.filter(id=request.data['chapter']).first().work
            return (work.comments_permitted and Common.user_is_blocked(work.user.id, request.user.id) is False)
        return False
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:            
            return True
        if 'chapter' in request.data:
            work = Chapter.objects.filter(id=request.data['chapter']).first().work
            return (work.comments_permitted and Common.user_is_blocked(work.user.id, request.user.id) is False)
        return False

class UserAllowsWorkAnonComments(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if isinstance(request.user, AnonymousUser):
            work = Chapter.objects.filter(id=request.data['chapter']).first().work
            return work.anon_comments_permitted
        else:
            return True
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:            
            return True

class UserAllowsBookmarkComments(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        bookmark = Bookmark.objects.filter(id=request.data['bookmark']).first()
        return (bookmark.comments_permitted and Common.user_is_blocked(bookmark.user.id, request.user.id) is False)
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:            
            return True
        bookmark = Bookmark.objects.filter(id=request.data['bookmark']).first()
        return (bookmark.comments_permitted and Common.user_is_blocked(bookmark.user.id, request.user.id) is False)

class UserAllowsBookmarkAnonComments(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if isinstance(request.user, AnonymousUser):
            bookmark = Bookmark.objects.filter(id=request.data['bookmark']).first()
            return bookmark.anon_comments_permitted
        else:
            return True
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:            
            return True
        if isinstance(request.user, AnonymousUser):
            bookmark = Bookmark.objects.filter(id=request.data['bookmark']).first()
            return bookmark.anon_comments_permitted
        else:
            return True

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:            
            return True

        return request.user.is_superuser

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_superuser

class IsUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user