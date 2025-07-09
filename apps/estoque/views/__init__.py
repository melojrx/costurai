# Importações das views para facilitar o uso
from .dashboard import EstoqueDashboardView
from .materia_prima import (
    MateriaPrimaListView,
    MateriaPrimaDetailView,
    MateriaPrimaCreateView,
    MateriaPrimaUpdateView,
    MateriaPrimaDeleteView,
    CategoriaMateriaPrimaListView,
    CategoriaMateriaPrimaCreateView,
    CategoriaMateriaPrimaUpdateView,
    CategoriaMateriaPrimaDeleteView,
)
from .movimentacao import (
    MovimentacaoEstoqueListView,
    MovimentacaoEstoqueDetailView,
    EntradaEstoqueCreateView,
    SaidaEstoqueCreateView,
    AjusteEstoqueCreateView,
    CancelarMovimentacaoView,
)
from .inventario import (
    InventarioFisicoListView,
    InventarioFisicoCreateView,
    InventarioFisicoDetailView,
    IniciarInventarioView,
    FinalizarInventarioView,
    CancelarInventarioView,
    ContarItemInventarioView,
    ResumoInventarioAPIView,
)
from .lote import (
    LoteMateriaPrimaListView,
    LoteMateriaPrimaCreateView,
    LoteMateriaPrimaDetailView,
    BloquearLoteView,
    DesbloquearLoteView,
)
from .relatorios import (
    RelatoriosEstoqueView,
    RelatorioEstoqueAtualView,
    RelatorioMovimentacoesView,
    RelatorioCustosView,
    RelatorioLotesVencimentoView,
)
from . import api

__all__ = [
    # Dashboard
    'EstoqueDashboardView',
    
    # Matérias-primas
    'MateriaPrimaListView',
    'MateriaPrimaDetailView',
    'MateriaPrimaCreateView',
    'MateriaPrimaUpdateView',
    'MateriaPrimaDeleteView',
    
    # Categorias
    'CategoriaMateriaPrimaListView',
    'CategoriaMateriaPrimaCreateView',
    'CategoriaMateriaPrimaUpdateView',
    'CategoriaMateriaPrimaDeleteView',
    
    # Movimentações
    'MovimentacaoEstoqueListView',
    'MovimentacaoEstoqueDetailView',
    'EntradaEstoqueCreateView',
    'SaidaEstoqueCreateView',
    'AjusteEstoqueCreateView',
    'CancelarMovimentacaoView',
    
    # Inventário
    'InventarioFisicoListView',
    'InventarioFisicoCreateView',
    'InventarioFisicoDetailView',
    'IniciarInventarioView',
    'FinalizarInventarioView',
    'CancelarInventarioView',
    'ContarItemInventarioView',
    'ResumoInventarioAPIView',
    
    # Lotes
    'LoteMateriaPrimaListView',
    'LoteMateriaPrimaCreateView',
    'LoteMateriaPrimaDetailView',
    'BloquearLoteView',
    'DesbloquearLoteView',
    
    # Relatórios
    'RelatoriosEstoqueView',
    'RelatorioEstoqueAtualView',
    'RelatorioMovimentacoesView',
    'RelatorioCustosView',
    'RelatorioLotesVencimentoView',
    
    # API
    'api',
] 