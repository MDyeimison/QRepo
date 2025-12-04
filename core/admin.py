from django.contrib import admin
from django.http import HttpResponse
from django_summernote.admin import SummernoteModelAdmin
from weasyprint import HTML

from .models import Post, AreaDoConhecimento, Dificuldade
from .utils import process_content_for_pdf 

def export_posts_to_pdf(modeladmin, request, queryset):
    
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
            /* Keeps the inline math locked to text height */
            img.latex-inline {
                height: 1.3em; 
                vertical-align: -0.3em;
                margin: 0 2px;
                display: inline-block;
            }

            /* --- BLOCK LATEX (\[ \]) --- */
            /* Now that Python generates it smaller, we just center it */
            img.latex-block {
                display: block;
                margin: 12px auto; /* Space above and below */
                height: auto;      /* Let it flow naturally */
                width: auto;       /* Prevent stretching */
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
    response['Content-Disposition'] = 'attachment; filename="posts_ABNT.pdf"'
    return response

export_posts_to_pdf.short_description = "Export PDF (ABNT Format)"

class PostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ('title', 'created_at')
    actions = [export_posts_to_pdf]

admin.site.register(Post, PostAdmin)

@admin.register(AreaDoConhecimento)
class AreaDoConhecimentoAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at', 'updated_at')
    search_fields = ('name',)
    fields = ('name', 'color', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Dificuldade)
class DificuldadeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at', 'updated_at')
    search_fields = ('name',)
    fields = ('name', 'color', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')