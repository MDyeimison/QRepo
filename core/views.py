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
                    /* Zero side margins on page to allow header/footer to span full width */
                    margin: 1.5cm 0cm 1.5cm 0cm; 
                    @top-center {
                        content: element(header);
                    }
                    @bottom-center {
                        content: element(footer);
                    }
                }

                body { 
                    font-family: Arial, Helvetica, sans-serif; 
                    font-size: 9pt; 
                    line-height: 1.4;
                    text-align: justify;
                    color: #000;
                    /* Add side margins to body instead */
                    margin-left: 1cm;
                    margin-right: 1cm;
                }

                /* Header & Footer */
                div.header {
                    position: running(header);
                    width: 100%;
                    border-bottom: 1px solid #000;
                    margin-bottom: 0;
                    padding-top: 0.8cm;
                    padding-bottom: 0;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 9pt;
                    /* Padding to align text with body content, while border spans full width */
                    padding-left: 1cm;
                    padding-right: 1cm;
                    box-sizing: border-box; 
                }

                div.footer {
                    position: running(footer);
                    width: 100%;
                    border-top: 1px solid #000;
                    margin-top: 0;
                    padding-top: 0;
                    padding-bottom: 0.8cm;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 9pt;
                    /* Padding to align text with body content */
                    padding-left: 1cm;
                    padding-right: 1cm;
                    box-sizing: border-box;
                }
                
                /* Use floats for splitting text */
                .left-text {
                    float: left;
                }
                
                .right-text {
                    float: right;
                }
                
                /* Clear floats if necessary, though usually not needed in fixed height running elements if simple */
                
                /* Page Counter */
                .pageNumber::after {
                    content: counter(page);
                }

                /* Columns */
                .content-columns {
                    column-count: 2;
                    column-gap: 1cm;
                    column-rule: 1px solid #000;
                    column-fill: auto; /* Fill first column before second */
                    width: 100%;
                }

                /* Question Styling */
                .question-item {
                    /* break-inside: avoid; Removed to allow questions to split and save space */
                    margin-bottom: 20px;
                }

                h1 { 
                    font-family: Arial, Helvetica, sans-serif; /* Sans-serif for question title */
                    font-size: 10pt; 
                    font-weight: bold; 
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    color: #000;
                    break-after: avoid; /* Keep title with content */
                }

                img { max-width: 100%; height: auto; display: block; margin: 10px auto; }

                /* LaTeX adjustments */
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

                .flex-container {
                    /* 1. Activate Flexbox */
                    display: flex;
                    
                    /* 2. Push items to opposite edges */
                    justify-content: space-between;
                    
                    /* 3. Vertically align text (optional but recommended) */
                    align-items: center;
                    
                    /* Ensure container takes full width */
                    width: 100%; 
                }

                .flex-container > div[style*="clear: both"] {
                    display: none;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="flex-container">
                    <div>Exame de Acesso ao Ensino Superior do Tocantins</div>
                    <div>EXATO 2025 – 2ª Edição</div>
                    <div style="clear: both;"></div>
                </div> 
            </div>

            <div class="footer">
                <div class="flex-container">
                    <div>Prova de Conhecimentos | TARDE</div>
                    <div><span class="pageNumber"></span></div>
                    <div style="clear: both;"></div>
                </div>
            </div>

            <div class="content-columns">
        """


        # Order by AreaDoConhecimento name to group them
        queryset = queryset.order_by('area_do_conhecimento__name', 'id')

        current_area = None
        for index, post in enumerate(queryset):
            processed_content = process_content_for_pdf(post.content)
            
            # Check if area has changed
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