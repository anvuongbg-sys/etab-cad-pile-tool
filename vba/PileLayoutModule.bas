'=============================================================================
' VBA Module: PileLayout
' Hệ thống vẽ móng cọc tự động trên AutoCAD từ dữ liệu CSV
' Hỗ trợ AutoCAD 2020-2026
' Tác giả: ETAB to CAD Tool
' Ngày: 2024
'=============================================================================

Option Explicit

' Khai báo các hằng số
Const PILE_LAYER = "PILE"
Const PILE_COLOR = 256  ' ByLayer
Const TEXT_HEIGHT = 0.3
Const CIRCLE_RADIUS = 0.4  ' Bán kính vòng tròn biểu thị cọc

' Structure lưu trữ dữ liệu cọc
Type PileData
    column_id As String
    pile_id As String
    X As Double
    Y As Double
    Z As Double
    Diameter As Double
    Length As Double
    bearing_capacity As Double
    load As Double
    utilization As Double
End Type

'=============================================================================
' SUB CHÍNH: Vẽ móng cọc từ file CSV
'=============================================================================
Sub PileLayout()
    
    Dim file_path As String
    Dim doc As AcadDocument
    Dim piles() As PileData
    Dim pile_count As Integer
    
    On Error GoTo ErrorHandler
    
    Set doc = ThisDrawing
    
    ' Mở dialog để chọn file CSV
    file_path = SelectCSVFile()
    
    If file_path = "" Then
        MsgBox "Không có file được chọn", vbExclamation, "Hủy"
        Exit Sub
    End If
    
    ' Kiểm tra file tồn tại
    If Dir(file_path) = "" Then
        MsgBox "File không tồn tại: " & file_path, vbCritical, "Lỗi"
        Exit Sub
    End If
    
    ' Tạo layer PILE nếu chưa có
    CreatePileLayer doc
    
    ' Đọc dữ liệu từ CSV
    pile_count = ReadPileDataFromCSV(file_path, piles)
    
    If pile_count = 0 Then
        MsgBox "Không tìm thấy dữ liệu cọc trong file", vbExclamation, "Lỗi"
        Exit Sub
    End If
    
    MsgBox "Tìm thấy " & pile_count & " cọc. Đang vẽ...", vbInformation, "Xác nhận"
    
    ' Vẽ các cọc
    Dim i As Integer
    doc.SendCommand "_ZOOM _E " & vbCr  ' Zoom extent
    
    For i = 0 To pile_count - 1
        DrawPile doc, piles(i)
    Next i
    
    ' Zoom fit all
    doc.SendCommand "_ZOOM _A " & vbCr
    
    MsgBox "Đã vẽ " & pile_count & " cọc thành công!", vbInformation, "Hoàn thành"
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Lỗi: " & Err.Description, vbCritical, "Lỗi"
End Sub

'=============================================================================
' Hàm: Chọn file CSV từ dialog
'=============================================================================
Function SelectCSVFile() As String
    
    Dim shell As Object
    Dim folder As Object
    Dim file As Object
    Dim file_path As String
    
    On Error GoTo ErrorHandler
    
    ' Tạo FileDialog (yêu cầu Scripting Runtime)
    ' Sử dụng Shell.BrowseForFolder thay thế
    Set shell = CreateObject("Shell.Application")
    
    ' Mặc định mở folder Desktop
    Dim desktop_path As String
    desktop_path = CreateObject("WScript.Shell").SpecialFolders("MyDocuments")
    
    ' Dùng lệnh Windows mở Open File Dialog
    file_path = BrowseForFile()
    
    SelectCSVFile = file_path
    
    Exit Function
    
ErrorHandler:
    SelectCSVFile = ""
End Function

'=============================================================================
' Hàm: Browse for file (dùng Windows API)
'=============================================================================
Function BrowseForFile() As String
    
    ' Tạo một file dialog bằng cách sử dụng VBScript
    Dim shell As Object
    Dim file_path As String
    Dim temp_script As String
    Dim temp_file As String
    Dim fso As Object
    
    On Error GoTo UseManualInput
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    temp_file = fso.GetSpecialFolder(2) & "\browse_file.vbs"  ' Temp folder
    
    ' Tạo VBScript để mở file dialog
    temp_script = "Set shell = CreateObject(\"Shell.Application\")" & vbCrLf & _
                  "Set fd = shell.BrowseForFolder(0, \"Chọn file pile_layout.csv:\", 0, 0)" & vbCrLf & _
                  "If Not fd Is Nothing Then" & vbCrLf & _
                  "  WScript.Echo fd.Self.Path" & vbCrLf & _
                  "End If"
    
    ' Ghi script vào file tạm
    Dim text_stream As Object
    Set text_stream = fso.CreateTextFile(temp_file, True)
    text_stream.Write temp_script
    text_stream.Close
    
    ' Chạy script
    Dim exec As Object
    Set exec = CreateObject("WScript.Shell").Exec("cscript.exe " & temp_file)
    file_path = exec.StdOut.ReadLine()
    
    ' Xóa file tạm
    On Error Resume Next
    fso.DeleteFile temp_file
    
    BrowseForFile = file_path
    Exit Function
    
UseManualInput:
    ' Nếu không thể dùng dialog, yêu cầu nhập đường dẫn
    BrowseForFile = InputBox("Nhập đường dẫn file CSV:", "Chọn File", "C:\\output\\pile_layout.csv")
End Function

'=============================================================================
' Hàm: Tạo Layer PILE
'=============================================================================
Sub CreatePileLayer(doc As AcadDocument)
    
    Dim layer As AcadLayer
    Dim found As Boolean
    
    On Error Resume Next
    
    ' Kiểm tra layer đã tồn tại
    found = False
    For Each layer In doc.Layers
        If layer.name = PILE_LAYER Then
            found = True
            Exit For
        End If
    Next layer
    
    ' Tạo layer nếu chưa tồn tại
    If Not found Then
        Set layer = doc.Layers.Add(PILE_LAYER)
        layer.Color = PILE_COLOR
        layer.Description = "Layer chứa dữ liệu cọc"
    End If
    
End Sub

'=============================================================================
' Hàm: Đọc dữ liệu cọc từ file CSV
'=============================================================================
Function ReadPileDataFromCSV(file_path As String, ByRef piles() As PileData) As Integer
    
    Dim fso As Object
    Dim file_obj As Object
    Dim text_stream As Object
    Dim line As String
    Dim parts() As String
    Dim line_count As Integer
    Dim i As Integer
    
    On Error GoTo ErrorHandler
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set file_obj = fso.GetFile(file_path)
    Set text_stream = file_obj.OpenAsTextStream(1, -2)  ' Read, System encoding
    
    line_count = 0
    ReDim piles(0)
    
    ' Đọc từng dòng
    Do While Not text_stream.AtEndOfStream
        line = text_stream.ReadLine()
        
        ' Bỏ qua dòng header
        If line_count > 0 And line <> "" Then
            parts = Split(line, ",")
            
            ' Kiểm tra có đủ cột không (tối thiểu 11 cột)
            If UBound(parts) >= 10 Then
                ReDim Preserve piles(line_count - 1)
                
                piles(line_count - 1).column_id = Trim(parts(0))
                piles(line_count - 1).pile_id = Trim(parts(1))
                piles(line_count - 1).X = CDbl(Trim(parts(2)))
                piles(line_count - 1).Y = CDbl(Trim(parts(3)))
                piles(line_count - 1).Z = CDbl(Trim(parts(4)))
                piles(line_count - 1).Diameter = CDbl(Trim(parts(5)))
                piles(line_count - 1).Length = CDbl(Trim(parts(6)))
                piles(line_count - 1).bearing_capacity = CDbl(Trim(parts(7)))
                piles(line_count - 1).load = CDbl(Trim(parts(8)))
                piles(line_count - 1).utilization = CDbl(Trim(parts(9)))
            End If
        End If
        
        line_count = line_count + 1
    Loop
    
    text_stream.Close
    
    ReadPileDataFromCSV = line_count - 1  ' Trừ đi dòng header
    
    Exit Function
    
ErrorHandler:
    ReadPileDataFromCSV = 0
    MsgBox "Lỗi đọc file: " & Err.Description, vbCritical, "Lỗi"
End Function

'=============================================================================
' Hàm: Vẽ một cọc
'=============================================================================
Sub DrawPile(doc As AcadDocument, pile As PileData)
    
    Dim circle As AcadCircle
    Dim text As AcadText
    Dim center(0 To 2) As Double
    Dim color_index As Integer
    
    On Error GoTo ErrorHandler
    
    ' Xác định màu dựa vào mức sử dụng
    If pile.utilization >= 90 Then
        color_index = 1  ' Red - nguy hiểm
    ElseIf pile.utilization >= 70 Then
        color_index = 3  ' Green - bình thường
    Else
        color_index = 5  ' Blue - có dư địa
    End If
    
    ' Tọa độ tâm cọc
    center(0) = pile.X
    center(1) = pile.Y
    center(2) = 0  ' Z=0 trên mặt vẽ CAD
    
    ' Vẽ vòng tròn biểu thị cọc
    Set circle = doc.ModelSpace.AddCircle(center, CIRCLE_RADIUS)
    circle.Layer = PILE_LAYER
    circle.Color = color_index
    circle.LineWeight = 35  ' 0.5mm
    
    ' Thêm text ghi ID cọc
    Dim text_position(0 To 2) As Double
    text_position(0) = pile.X
    text_position(1) = pile.Y - CIRCLE_RADIUS - TEXT_HEIGHT
    text_position(2) = 0
    
    Set text = doc.ModelSpace.AddText(pile.pile_id, text_position, TEXT_HEIGHT)
    text.Layer = PILE_LAYER
    text.Color = color_index
    text.HorizontalAlignment = acAlignmentCenter
    text.VerticalAlignment = acAlignmentTop
    
    Exit Sub
    
ErrorHandler:
    ' Bỏ qua lỗi và tiếp tục vẽ cọc tiếp theo
End Sub

'=============================================================================
' SUB: Xóa tất cả cọc
'=============================================================================
Sub ClearPiles()
    
    Dim doc As AcadDocument
    Dim obj As AcadEntity
    Dim i As Integer
    
    Set doc = ThisDrawing
    
    On Error Resume Next
    
    ' Xóa tất cả object trên layer PILE
    For i = doc.ModelSpace.Count - 1 To 0 Step -1
        Set obj = doc.ModelSpace(i)
        If obj.Layer = PILE_LAYER Then
            obj.Delete
        End If
    Next i
    
    MsgBox "Đã xóa tất cả cọc trên layer " & PILE_LAYER, vbInformation, "Hoàn thành"
    
End Sub

'=============================================================================
' SUB: Hiển thị thông tin cọc được chọn
'=============================================================================
Sub ShowPileInfo()
    
    Dim doc As AcadDocument
    Dim sel_set As AcadSelectionSet
    Dim obj As AcadEntity
    
    Set doc = ThisDrawing
    
    On Error Resume Next
    
    ' Xóa selection set cũ nếu tồn tại
    doc.SelectionSets.Item("TempSelSet").Delete
    
    ' Tạo selection set mới
    Set sel_set = doc.SelectionSets.Add("TempSelSet")
    
    ' Yêu cầu chọn object
    MsgBox "Chọn các cọc để xem thông tin. Nhấn ESC để hoàn thành.", vbInformation, "Chọn"
    
    Dim filter_type(0) As Integer
    Dim filter_data(0) As Variant
    filter_type(0) = 8  ' Entity type = Circle
    filter_data(0) = "CIRCLE"
    
    sel_set.SelectOnScreen filter_type, filter_data
    
    If sel_set.Count = 0 Then
        MsgBox "Không có cọc được chọn", vbInformation, "Thông báo"
    Else
        MsgBox "Đã chọn " & sel_set.Count & " cọc. Xem trên layer " & PILE_LAYER, vbInformation, "Kết quả"
    End If
    
    sel_set.Delete
    
End Sub

'=============================================================================
' SUB: Tối ưu hóa view
'=============================================================================
Sub OptimizeView()
    
    Dim doc As AcadDocument
    
    Set doc = ThisDrawing
    
    ' Zoom Extents
    doc.SendCommand "_ZOOM _E " & vbCr
    
    ' Freeze tất cả layer trừ PILE
    Dim layer As AcadLayer
    For Each layer In doc.Layers
        If layer.name <> PILE_LAYER And layer.name <> "0" Then
            layer.Freeze = True
        End If
    Next layer
    
    ' Regenerate
    doc.SendCommand "_REGEN " & vbCr
    
    MsgBox "Đã tối ưu view. Chỉ hiển thị layer " & PILE_LAYER, vbInformation, "Hoàn thành"
    
End Sub
