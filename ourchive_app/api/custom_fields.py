from rest_framework import serializers

class PrivateField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        if instance.user == self.context['request'].user:
            return super(PrivateField, self).get_attribute(instance)
        return None

class UserPrivateField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        if instance == self.context['request'].user:
            return super(PrivateField, self).get_attribute(instance)
        return None