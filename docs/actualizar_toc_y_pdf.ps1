# Abre el .docx con Microsoft Word, actualiza la tabla de contenido y los campos,
# guarda el documento y exporta un PDF al lado. Requiere Word instalado (Windows).
#
#   powershell -File docs/actualizar_toc_y_pdf.ps1 [ruta\al\documento.docx]
param(
    [string]$Docx = (Join-Path $PSScriptRoot 'Documentacion_Sistema_Inventarios_Manaudi.docx')
)
$Docx = (Resolve-Path $Docx).Path
$Pdf = [System.IO.Path]::ChangeExtension($Docx, '.pdf')

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx)
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    $doc.Fields.Update() | Out-Null
    foreach ($seccion in $doc.Sections) {
        foreach ($pie in $seccion.Footers) { $pie.Range.Fields.Update() | Out-Null }
    }
    $doc.Save()
    $doc.ExportAsFixedFormat($Pdf, 17)   # 17 = wdExportFormatPDF
    "Páginas: $($doc.ComputeStatistics(2))"  # 2 = wdStatisticPages
    $doc.Close(0)
    "Guardado: $Docx"
    "PDF:      $Pdf"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
