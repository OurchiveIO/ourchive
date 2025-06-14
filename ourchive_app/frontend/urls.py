from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index),
    path('search/', views.search),
    path('search/filter', views.search_filter),
    path('works/', views.works, name='fe-all-works'),
    path('works/new/', views.new_work, name='fe-new-work'),
    path('works/<int:id>/edit/', views.edit_work, name='edit-work'),
    path('works/<int:id>/publish/', views.publish_work, name='publish-work'),
    path('works/<int:id>/publish-full/', views.publish_work_and_chapters, name='publish-full'),
    path('works/<int:pk>/export/<str:file_ext>', views.export_work, name='export-work'),
    path('works/type/<int:type_id>', views.works_by_type),
    path('works/<int:pk>/', views.work, name='fe-work-view'),
    path('works/<int:pk>/<int:chapter_offset>', views.work),
    path('works/<int:work_id>/delete', views.delete_work, name='delete-work'),
    path('works/<int:work_id>/chapters/<int:chapter_id>/delete', views.delete_chapter, name='delete-chapter'),
    path('works/<int:work_id>/chapters/<int:chapter_id>/publish/', views.publish_chapter),
    path('bookmark-collections/', views.bookmark_collections),
    path('bookmark-collections/collection-eligible-bookmarks', views.get_bookmarks_for_collection, name='collection-eligible-bookmarks'),
    path('bookmark-collections/new', views.new_bookmark_collection, name='fe-new-collection'),
    path('bookmark-collections/<int:pk>/edit', views.edit_bookmark_collection),
    path('bookmark-collections/<int:pk>/', views.bookmark_collection, name='fe-view-collection'),
    path('bookmark-collections/<int:pk>/delete', views.delete_bookmark_collection, name='delete-bookmark-collection'),
    path('bookmark-collections/<int:pk>/publish', views.publish_bookmark_collection, name='publish-bookmark-collection'),
    path('bookmark-collections/<int:pk>/comments', views.render_collection_comments),
    path('bookmark-collections/<int:pk>/comments/new', views.create_collection_comment),
    path('bookmark-collections/<int:pk>/comments/edit', views.edit_collection_comment),
    path('bookmark-collections/<int:pk>/comments/<int:comment_id>/delete', views.delete_collection_comment, name='delete-collection-comment'),
    path('bookmarks/', views.bookmarks),
    path('bookmarks/<int:pk>/', views.bookmark, name='fe-view-bookmark'),
    path('bookmarks/<int:pk>/add-collection/', views.add_collection_to_bookmark, name='fe-add-collection-to-bookmark'),
    path('bookmarks/<int:pk>/comments', views.render_bookmark_comments),
    path('bookmarks/<int:pk>/comments/new', views.create_bookmark_comment),
    path('bookmarks/<int:pk>/comments/edit', views.edit_bookmark_comment),
    path('bookmarks/<int:pk>/comments/<int:comment_id>/delete', views.delete_bookmark_comment, name='delete-bookmark-comment'),
    path('bookmarks/<int:pk>/edit', views.edit_bookmark),
    path('bookmarks/<int:id>/publish/', views.publish_bookmark),
    path('bookmarks/<int:bookmark_id>/delete', views.delete_bookmark, name='delete-bookmark'),
    path('bookmarks/new/<int:work_id>', views.new_bookmark),
    path('login/', views.log_in, name='fe-login'),
    path('register/', views.register, name='fe-register-account'),
    path('request-invite/', views.request_invite),
    path('logout/', views.log_out),
    path('reset-password/', auth_views.PasswordResetView.as_view(template_name="reset_password.html"), name='fe-reset-password'),
    path('reset-password/done/', auth_views.PasswordResetDoneView.as_view(template_name="reset_password_done.html"), name='password_reset_done'),
    path('reset-password/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="reset_password_confirm.html"), name='password_reset_confirm'),
    path('reset-password/complete/', auth_views.PasswordResetCompleteView.as_view(template_name="reset_password_complete.html"), name='password_reset_complete'),
    path('change-password/', auth_views.PasswordChangeView.as_view(template_name="change_password.html"), name='password_change'),
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(template_name="change_password_done.html"), name='password_change_done'),
    path('username/<int:pk>/', views.user_name, name='user-profile-parent'),
    path('users/<str:username>/import', views.import_works, name='fe-import-works'),
    path('users/<str:username>/save-search', views.search_save),
    path('users/<int:pk>/import-status', views.import_works_status, name='fe-import-works-status'),
    path('username/<int:pk>/edit', views.edit_user, name='fe-user-profile-edit'),
    path('username/<int:pk>/account/edit', views.edit_account, name='fe-user-account-edit'),
    path('username/<str:username>/works/', views.user_works, name='fe-user-works'),
    path('username/<str:username>/works/drafts/', views.user_works_drafts),
    path('username/<str:username>/bookmarks/', views.user_bookmarks, name='fe-user-bookmarks'),
    path('username/<str:username>/bookmark-collections/', views.user_bookmark_collections, name='fe-user-collections'),
    path('username/<str:username>/bookmarks/drafts/', views.user_bookmarks_drafts),
    path('username/<str:username>/notifications/', views.user_notifications),
    path('username/<str:username>/notifications/<int:notification_id>/read', views.mark_notification_read),
    path('username/<str:username>/notifications/<int:notification_id>/delete', views.delete_notification),
    path('username/<str:username>/notifications/read', views.user_notifications_all_read, name='fe-notifications-mark-all-read'),
    path('username/<str:username>/notifications/delete-all', views.user_notifications_delete_all, name='fe-notifications-delete-all'),
    path('users/<str:username>/series/', views.user_series, name='fe-user-series'),
    path('users/<str:username>/anthologies/', views.user_anthologies, name='fe-user-anthologies'),
    path('users/<str:username>/blocklist', views.user_block_list, name='fe-user-blocklist'),
    path('users/<int:user_id>/blocks/<int:pk>/unblock', views.unblock_user, name='fe-unblock-user'),
    path('users/<int:pk>/block', views.block_user, name='fe-block-user'),
    path('users/<str:username>/delete', views.delete_user),
    path('users/<str:username>/report', views.report_user, name='report-user'),
    path('users/<str:username>/subscriptions', views.user_subscriptions, name='fe-user-subscriptions'),
    path('users/<str:username>/subscriptions/unsubscribe', views.unsubscribe, name='fe-unsubscribe'),
    path('users/subscriptions/subscribe', views.subscribe, name='fe-subscribe'),
    path('users/<str:username>/subscriptions/bookmarks', views.user_bookmark_subscriptions, name='fe-user-bookmark-subscriptions'),
    path('users/<str:username>/subscriptions/collections', views.user_collection_subscriptions, name='fe-user-collection-subscriptions'),
    path('users/<str:username>/subscriptions/works', views.user_work_subscriptions, name='fe-user-work-subscriptions'),
    path('users/<str:username>/subscriptions/series', views.user_series_subscriptions, name='fe-user-series-subscriptions'),
    path('users/<str:username>/subscriptions/anthologies', views.user_anthology_subscriptions, name='fe-user-anthology-subscriptions'),
    path('users/<str:username>/savedsearches', views.user_saved_searches, name='fe-user-saved-searches'),
    path('savedsearch/<int:pk>', views.saved_search, name='fe-saved-search'),
    path('savedsearch/filter', views.saved_search_filter, name='fe-saved-search-filter'),
    path('works/<int:work_id>/chapters/<int:id>/edit', views.edit_chapter),
    path('works/<int:work_id>/chapters/new', views.new_chapter),
    path('workcomments/<int:work_id>/chapter/<int:chapter_id>', views.render_work_comments),
    path('works/<int:work_id>/chapters/<int:chapter_id>/<int:chapter_offset>/comments', views.render_chapter_comments),
    path('works/<int:work_id>/chapters/<int:chapter_id>/comments/new', views.create_chapter_comment),
    path('works/<int:work_id>/chapters/<int:chapter_id>/comments/edit', views.edit_chapter_comment),
    path('works/<int:work_id>/chapters/<int:chapter_id>/comments/<int:comment_id>/delete', views.delete_chapter_comment, name='delete-chapter-comment'),
    path('tags/<int:tag>', views.works_by_tag, name='tag-results'),
    path('tags/<int:tag_id>/next', views.works_by_tag_next),
    path('attributes/<int:attribute>', views.works_by_attribute, name='attribute-results'),
    path('fingerguns/<int:work_id>', views.new_fingerguns),
    path('switch-css-mode/', views.switch_css_mode, name='switch-css-mode'),
    path('tag-autocomplete', views.tag_autocomplete),
    path('language-autocomplete', views.language_autocomplete),
    path('bookmark-autocomplete', views.bookmark_autocomplete),
    path('user-autocomplete', views.user_autocomplete),
    path('content-pages/<int:pk>', views.content_page, name='fe-content-page'),
    path('accept-cookies', views.accept_cookies, name='accept-cookies'),
    path('export-chives', views.export_chives, name='fe-export-chives'),
    path('users/remove-cocreator', views.remove_as_cocreator, name='fe-remove-as-cocreator'),
    path('users/approve-cocreator', views.approve_as_cocreator, name='fe-approve-as-cocreator'),
    path('users/cocreator-approvals', views.cocreator_approvals, name='fe-view-approvals'),
    path('users/cocreator-approvals/bulk-approve', views.bulk_approve_cocreator, name='fe-cocreator-bulk-approve'),
    path('users/cocreator-approvals/bulk-reject', views.bulk_reject_cocreator, name='fe-cocreator-bulk-reject'),
    path('news', views.news_list, name='fe-news-list'),
    path('news/<int:pk>', views.news, name='fe-news-detail'),
    path('series/create', views.create_series, name='fe-create-series'),
    path('series/<int:pk>/edit', views.edit_series, name='fe-edit-series'),
    path('series-autocomplete', views.series_autocomplete, name='fe-series-autocomplete'),
    path('series/<int:pk>', views.series, name='fe-series'),
    path('series/<int:pk>/delete', views.delete_series, name='delete-series'),
    path('series/<int:pk>/work/<int:work_id>/delete', views.delete_work_series, name='delete-work-series'),
    path('series/<int:pk>/works/render', views.render_series_work, name='fe-series-work-render'),
    path('anthologies/create', views.create_anthology, name='fe-create-anthology'),
    path('anthologies/<int:pk>/edit', views.edit_anthology, name='fe-edit-anthology'),
    path('anthologies-autocomplete', views.anthology_autocomplete, name='fe-anthology-autocomplete'),
    path('anthologies/<int:pk>', views.anthology, name='fe-anthology'),
    path('anthologies/<int:pk>/delete', views.delete_anthology, name='delete-anthology'),
    path('anthologies/<int:pk>/work/<int:work_id>/delete', views.delete_work_anthology, name='delete-work-anthology'),
    path('anthologies/<int:pk>/works/render', views.render_anthology_work, name='fe-anthology-work-render'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
