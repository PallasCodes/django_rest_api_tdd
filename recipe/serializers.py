from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name'
        )
        read_only_fields = ('id',)
        

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name'
        )
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.PrimaryKeyRelatedField(
        many = True,
        queryset = Ingredient.objects.all()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many = True,
        queryset = Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'title',
            'ingredients',
            'time_minutes',
            'price',
            'tags',
            'link'
        )
        read_only_fields =  ('id',)


class RecipeDetailSerializer(RecipeSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)


class RecipeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'image'
        )
        read_only_fields = ('id',)
