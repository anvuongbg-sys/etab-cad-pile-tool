# Data Examples

Place your ETAB export files here:

## Expected CSV Format

```csv
Joint,X,Y,Z,LoadCase,Px,Py,Pz,Mx,My,Mz
C1,0,0,0,LC1,-10,-15,-1000,50,60,10
C2,10,0,0,LC1,-12,-18,-1200,55,65,12
C3,5,8,0,LC1,-8,-12,-800,40,50,8
```

## Column Description

| Column | Description | Unit |
|--------|-------------|------|
| Joint | Column ID | - |
| X | X coordinate | m |
| Y | Y coordinate | m |
| Z | Z coordinate | m |
| LoadCase | Load case name | - |
| Px | Force X (horizontal) | t (tấn) |
| Py | Force Y (horizontal) | t (tấn) |
| Pz | Force Z (vertical) | t (tấn) |
| Mx | Moment X | t.m |
| My | Moment Y | t.m |
| Mz | Moment Z | t.m |

## How to Export from ETAB

1. Open your ETAB model (.edb)
2. Go to **File** → **Export** → **Results**
3. Select **Joint Forces**
4. Choose output format:
   - CSV: Export as text (recommended)
   - Excel: For larger datasets
5. Save to this directory
6. Run the tool:
   ```bash
   python main.py data/<your_file>.csv
   ```
