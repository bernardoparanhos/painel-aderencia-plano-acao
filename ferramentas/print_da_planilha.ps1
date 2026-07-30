# Exporta a aba Resumo da planilha como imagem, usando o próprio Excel.
#
# O print que vai para o site e para o LinkedIn precisa ser a planilha de verdade,
# não uma reconstrução do painel em outra ferramenta. Este script abre o arquivo,
# recorta o intervalo do painel e salva em PNG — o mesmo que uma captura de tela,
# só que sem barra de fórmulas, sem cabeçalho de coluna e sempre do mesmo tamanho.
#
# Uso (Windows, com Excel instalado):
#   powershell -ExecutionPolicy Bypass -File ferramentas\print_da_planilha.ps1
#
# Sem Excel instalado, ignore: as imagens de exemplos/prints/ geradas pelo Python
# cobrem o mesmo material.

param(
    [string]$Planilha = "saida\painel_aderencia.xlsx",
    [string]$Aba      = "Resumo",
    [string]$Intervalo = "A1:P46",
    [string]$Destino  = "exemplos\prints\planilha-resumo.png"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$caminhoPlanilha = Join-Path $raiz $Planilha
$caminhoDestino  = Join-Path $raiz $Destino

if (-not (Test-Path $caminhoPlanilha)) {
    throw "Planilha não encontrada em $caminhoPlanilha. Rode antes: python src\main.py"
}
$pastaDestino = Split-Path -Parent $caminhoDestino
if (-not (Test-Path $pastaDestino)) { New-Item -ItemType Directory -Force $pastaDestino | Out-Null }

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    # aberto para escrita de propósito: o recorte precisa de um objeto gráfico temporário
    # na aba, e o Excel não deixa criar um em pasta somente-leitura. Nada é salvo.
    $wb = $excel.Workbooks.Open($caminhoPlanilha)
    $ws = $wb.Worksheets.Item($Aba)
    $ws.Activate()

    $faixa = $ws.Range($Intervalo)
    # xlScreen = 1, xlBitmap = 2 — bitmap preserva as cores exatamente como na tela
    $faixa.CopyPicture(1, 2)
    Start-Sleep -Milliseconds 700   # o Excel leva um instante para publicar na área de transferência

    # a imagem é lida direto da área de transferência. O caminho pelo objeto gráfico do
    # próprio Excel existe e é o mais citado, mas exporta em branco quando a aba tem
    # gráficos sobrepostos ao recorte — que é exatamente o caso desta.
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $imagem = [System.Windows.Forms.Clipboard]::GetImage()
    if ($null -eq $imagem) { throw "A área de transferência voltou vazia; o recorte não foi copiado." }
    $imagem.Save($caminhoDestino, [System.Drawing.Imaging.ImageFormat]::Png)
    $imagem.Dispose()

    $wb.Close($false)
    Write-Host "print salvo em $Destino"
}
finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    [GC]::Collect()
}
