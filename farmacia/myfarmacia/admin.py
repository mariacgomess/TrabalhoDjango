from django.contrib import admin
from .models import TodoItem
from .models import Banco
from .models import TipoSangue
from .models import Dador
from .models import Componente
from .models import PostoRecolha
from .models import Doacao
from .models import Hospital
from .models import Pedido
from .models import LinhaPedido

# Register your models here.
admin.site.register(TodoItem)
admin.site.register(Banco)
admin.site.register(TipoSangue)
admin.site.register(Dador)
admin.site.register(Componente)
admin.site.register(PostoRecolha)
admin.site.register(Doacao)
admin.site.register(Hospital)
admin.site.register(Pedido)
admin.site.register(LinhaPedido)

print("ola")