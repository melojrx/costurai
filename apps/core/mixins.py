from django.db import models


class TenantMixin:
    """
    Mixin para ViewSets que automaticamente filtra objetos pela empresa do usuário logado.
    Garante isolamento de dados em ambiente multitenant.
    """
    
    def get_queryset(self):
        """
        Filtra o queryset pela empresa atual do usuário.
        Deve ser sobrescrito nas views filhas conforme necessário.
        """
        queryset = super().get_queryset()
        
        # Se o usuário tem empresa_atual definida, filtrar por ela
        if hasattr(self.request, 'empresa_atual') and self.request.empresa_atual:
            empresa = self.request.empresa_atual
            
            # Verificar se o model tem campo empresa
            if hasattr(queryset.model, 'empresa'):
                return queryset.filter(empresa=empresa)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Automaticamente associa a empresa atual ao objeto sendo criado.
        """
        if hasattr(self.request, 'empresa_atual') and self.request.empresa_atual:
            # Verificar se o serializer aceita empresa
            if 'empresa' in serializer.validated_data or hasattr(serializer.Meta.model, 'empresa'):
                serializer.save(empresa=self.request.empresa_atual)
                return
        
        super().perform_create(serializer) 