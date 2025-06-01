from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'  # Parámetro para cambiar tamaño de página
    max_page_size = 10  # Límite máximo para evitar abusos
    
    def get_page_size(self, request):
        # Obtener el tamaño de página del query parameter
        page_size = request.query_params.get(self.page_size_query_param)
        
        if page_size and page_size.isdigit():
            print(f"Usando page_size personalizado: {page_size}")
            return int(page_size)
        
        print("Usando page_size por defecto")
        return self.page_size