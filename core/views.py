from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import Post, AreaDoConhecimento
from .forms import PostForm

class PostListView(ListView):
    model = Post
    template_name = 'index.html'
    context_object_name = 'posts'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query (name/title)
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        
        # Filter by AreaDoConhecimento
        area_id = self.request.GET.get('area', '')
        if area_id:
            queryset = queryset.filter(area_do_conhecimento_id=area_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm()
        context['areas'] = AreaDoConhecimento.objects.all().order_by('name')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_area'] = self.request.GET.get('area', '')
        return context

class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'index.html'
    success_url = reverse_lazy('index')

    def form_invalid(self, form):
        return super().form_invalid(form)

from django.http import HttpResponse
from weasyprint import HTML
from .utils import process_content_for_pdf

def export_selected_pdf(request):
    if request.method == 'POST':
        post_ids = request.POST.getlist('post_ids')
        queryset = Post.objects.filter(id__in=post_ids)
        
        html_string = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page { 
                    size: A4; 
                    margin: 3cm 2cm 2cm 3cm; 
                }

                body { 
                    font-family: "Times New Roman", Times, serif; 
                    font-size: 12pt; 
                    line-height: 1.5;
                    text-align: justify;
                    color: #000;
                }
                
                h1 { 
                    font-size: 14pt; 
                    font-weight: bold; 
                    text-align: center;
                    text-transform: uppercase;
                    margin-bottom: 1cm;
                }

                img { max-width: 100%; height: auto; }

                /* --- INLINE LATEX ($$) --- */
                img.latex-inline {
                    height: 1.3em; 
                    vertical-align: -0.3em;
                    margin: 0 2px;
                    display: inline-block;
                }

                /* --- BLOCK LATEX (\[ \]) --- */
                img.latex-block {
                    display: block;
                    margin: 12px auto; 
                    height: auto;      
                    width: auto;       
                }
                
                p { text-indent: 1.25cm; margin: 0 0 10px 0; }
                .page-break { page-break-after: always; }
            </style>
        </head>
        <body>
        """

        total = queryset.count()
        for index, post in enumerate(queryset):
            processed_content = process_content_for_pdf(post.content)
            
            html_string += f"""
            <div class="post-wrapper">
                <h1>{post.title}</h1>
                <div style="text-align: right; font-size: 10pt; margin-bottom: 1cm;">
                    {post.created_at.strftime('%d de %B de %Y')}
                </div>
                <div class="content">
                    {processed_content}
                </div>
            </div>
            """
            if index < total - 1:
                html_string += '<div class="page-break"></div>'

        html_string += "</body></html>"

        pdf_file = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="questoes_selecionadas.pdf"'
        return response
    
    return redirect('index')

def generate_exam_pdf(request):
    if request.method == 'POST':
        post_ids = request.POST.getlist('post_ids')
        queryset = Post.objects.filter(id__in=post_ids)
        
        html_string = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page { 
                    size: A4; 
                    /* MARGINS ADJUSTED: 
                       Top/Bottom: 1cm (Requested reduction)
                       Left/Right: 1cm 
                    */
                    margin: 1cm 1cm 1cm 1cm; 

                    @top-center {
                        content: element(header);
                        vertical-align: bottom; /* Sit at the line */
                        width: 100%;
                    }
                    @bottom-center {
                        content: element(footer);
                        vertical-align: top; /* Sit at the line */
                        width: 100%;
                    }
                }

                body { 
                    font-family: Arial, Helvetica, sans-serif; 
                    font-size: 9pt; 
                    line-height: 1.4;
                    text-align: justify;
                    color: #000;
                    margin: 0; 
                }

                /* --- 1. VERTICAL LINE (Fixed Position) --- */
                .vertical-line {
                    position: fixed;
                    left: 50%;
                    
                    /* Extend to absolute edges (0) to guarantee connection */
                    top: 0; 
                    bottom: 0; 
                    
                    border-left: 1px solid #000; 
                    z-index: -10; 
                }

                /* --- 2. HEADER & FOOTER --- */
                div.header {
                    position: running(header);
                    width: 100%;
                    border-bottom: 1px solid #000;
                    
                    /* Padding creates the white space that masks the vertical line.
                       Since margin is now 1cm, we use ~0.4cm padding so the 
                       text + padding fits nicely in that 1cm space. */
                    padding-top: 0.4cm; 
                    padding-bottom: 5px; 
                    
                    margin-bottom: 0;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 9pt;
                    background-color: white; 
                }

                div.footer {
                    position: running(footer);
                    width: 100%;
                    border-top: 1px solid #000;
                    
                    /* Padding creates the white space that masks the vertical line. */
                    padding-bottom: 0.4cm;
                    padding-top: 5px; 
                    
                    margin-top: 0;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 9pt;
                    background-color: white;
                }
                
                table.layout-table {
                    width: 100%;
                    border-collapse: collapse;
                    border: none;
                }
                td.left { text-align: left; width: 50%; }
                td.right { text-align: right; width: 50%; }

                .pageNumber::after {
                    content: counter(page);
                }

                /* Columns */
                .content-columns {
                    column-count: 2;
                    column-gap: 1cm;
                    column-fill: auto; 
                    width: 100%;
                    padding-top: 10px; /* Reduced slightly to match tighter layout */
                }

                /* Question Styling */
                .question-item {
                    margin-bottom: 20px;
                }

                h1 { 
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 10pt; 
                    font-weight: bold; 
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    color: #000;
                    break-after: avoid; 
                }
                
                .area-header {
                    break-after: avoid;
                }

                img { max-width: 100%; height: auto; display: block; margin: 10px auto; }
                
                img.latex-inline {
                    height: 1.2em; 
                    vertical-align: -0.3em;
                    display: inline-block;
                    margin: 0 2px;
                }
                img.latex-block {
                    display: block;
                    margin: 10px auto;
                    transform: scale(0.6);
                    transform-origin: center;
                }
                
                p { margin: 0 0 8px 0; }
            </style>
        </head>
        <body>
            <div class="vertical-line"></div>

            <div class="header">
                <table class="layout-table">
                    <tr>
                        <td class="left">Exame de Acesso ao Ensino Superior do Tocantins</td>
                        <td class="right">EXATO 2025 – 2ª Edição</td>
                    </tr>
                </table>
            </div>

            <div class="footer">
                <table class="layout-table">
                    <tr>
                        <td class="left">Prova de Conhecimentos | TARDE</td>
                        <td class="right"><span class="pageNumber"></span></td>
                    </tr>
                </table>
            </div>

            <div class="content-columns">
        """

        queryset = queryset.order_by('area_do_conhecimento__name', 'id')

        current_area = None
        for index, post in enumerate(queryset):
            processed_content = process_content_for_pdf(post.content)
            
            if post.area_do_conhecimento != current_area:
                current_area = post.area_do_conhecimento
                area_name = current_area.name if current_area else "Sem Área"
                html_string += f"""
                <div class="area-header" style="background-color: grey; color: white; padding: 5px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; text-transform: uppercase;">
                    {area_name}
                </div>
                """

            html_string += f"""
            <div class="question-item">
                <h1 style="background-color:lightgrey;">QUESTÃO {index + 1:02d}</h1>
                <div class="content">
                    {processed_content}
                </div>
            </div>
            """

        html_string += """
            </div>
        </body>
        </html>
        """

        pdf_file = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="prova_gerada.pdf"'
        return response
    
    return redirect('index')