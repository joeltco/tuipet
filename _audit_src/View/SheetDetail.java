/*
 * Decompiled with CFR 0.152.
 */
package View;

public class SheetDetail {
    private int _sheetWidth;
    private int _sheetHeight;
    private int _sheetRows;
    private int _sheetColumns;
    private int _emptyPixels;

    public int getSheetWidth() {
        return this._sheetWidth;
    }

    public int getSheetHeight() {
        return this._sheetHeight;
    }

    public int getSheetRows() {
        return this._sheetRows;
    }

    public int getSheetColumns() {
        return this._sheetColumns;
    }

    public int getEmptyPixels() {
        return this._emptyPixels;
    }

    public SheetDetail(int sheetWidth, int sheetHeight, int sheetRows, int sheetColumns, int emptyPixels) {
        this._sheetWidth = sheetWidth;
        this._sheetHeight = sheetHeight;
        this._sheetRows = sheetRows;
        this._sheetColumns = sheetColumns;
        this._emptyPixels = emptyPixels;
    }
}

