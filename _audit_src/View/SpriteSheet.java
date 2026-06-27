/*
 * Decompiled with CFR 0.152.
 */
package View;

import Model.ViewSettings;
import View.SheetDetail;
import View.SpriteObjWIP;
import View.ViewUtil;
import java.awt.image.BufferedImage;
import java.util.HashMap;
import javax.swing.ImageIcon;
import javax.swing.JPanel;

public class SpriteSheet
extends SpriteObjWIP {
    private int _spriteColumn;
    private int _spriteRow;
    private SheetDetail _currentAltSheet;
    private int _sheetWidth;
    private int _sheetHeight;
    private int _sheetRows;
    private int _sheetColumns;
    private int _emptyPixels;
    private ImageIcon[] _sheet;
    private ImageIcon[] _sheetMirror;
    private final HashMap<String, SheetDetail> _altSheets = new HashMap();

    public ImageIcon[] getSheet() {
        return this._sheet;
    }

    public void setSheet(ImageIcon[] s) {
        this._sheet = s;
    }

    public HashMap<String, SheetDetail> getAltSheets() {
        return this._altSheets;
    }

    public ImageIcon[] getSheetMirror() {
        return this._sheetMirror;
    }

    public void setSheetMirror(ImageIcon[] s) {
        this._sheetMirror = s;
    }

    public SheetDetail getCurrentAltSheet() {
        return this._currentAltSheet;
    }

    public int getSpriteColumn() {
        return this._spriteColumn;
    }

    public void setSpriteColumn(int newNum) {
        this._spriteColumn = newNum;
    }

    public int getSpriteRow() {
        return this._spriteRow;
    }

    public void setSpriteRow(int row) {
        this._spriteRow = row;
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

    public int getSheetWidth() {
        return this._sheetWidth;
    }

    public int getSheetHeight() {
        return this._sheetHeight;
    }

    public SpriteSheet(String firstLoc, String secondLoc, String fileNameAndExtension, JPanel pane, int spriteWidth, int spriteHeight, ViewSettings view) {
        super(firstLoc, secondLoc, fileNameAndExtension, pane, spriteWidth, spriteHeight, view);
        this._width = spriteWidth;
        this._height = spriteHeight;
    }

    public SpriteSheet(String firstLoc, String secondLoc, String fileNameAndExtension, JPanel pane, int spriteWidth, int spriteHeight, ViewSettings view, double spriteRescale) {
        super(firstLoc, secondLoc, fileNameAndExtension, pane, spriteWidth, spriteHeight, view, spriteRescale);
        this._width = spriteWidth;
        this._height = spriteHeight;
    }

    public void addAltSprite(String name, String location, float opacity, double spriteRescale, boolean isMirror, int sheetWidth, int sheetHeight, int sheetRows, int sheetColumns, int emptyPixels, int width, int height) {
        this._altSheets.put(name, new SheetDetail(sheetWidth, sheetHeight, sheetRows, sheetColumns, emptyPixels));
        super.addAltSprite(name, location, opacity, spriteRescale, isMirror, width, height);
    }

    @Override
    public void setAltSprite(String name) {
        super.setAltSprite(name);
        if (this._altSheets.containsKey(name)) {
            SheetDetail s;
            this._currentAltSheet = s = this._altSheets.get(name);
            this._sheetWidth = s.getSheetWidth();
            this._sheetHeight = s.getSheetHeight();
            this._sheetRows = s.getSheetRows();
            this._sheetColumns = s.getSheetColumns();
            this._emptyPixels = s.getEmptyPixels();
        }
    }

    public void drawAltSheet(String name, int spriteRow, boolean isMirror) {
        this.setAltSprite(name);
        this.drawFromSheet(spriteRow, isMirror);
    }

    public void drawAltSheet(String name) {
        this.setAltSprite(name);
        this.drawFromSheet(this._spriteColumn, this._isMirror);
    }

    public void drawFromSheet(int spriteRow, boolean isMirror, String spriteNameAndExtension) {
        this.drawFromSheet(spriteRow, isMirror, spriteNameAndExtension, this._spriteRescale);
    }

    public void drawFromSheet(int spriteRow, boolean isMirror, String spriteNameAndExtension, double rescale) {
        try {
            this._spriteRow = spriteRow;
            this._isMirror = isMirror;
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        this.update();
    }

    public void drawFromSheet(int spriteRow, boolean isMirror) {
        this.drawFromSheet(spriteRow, isMirror, this._spriteNameAndExtension);
    }

    public void drawFromSheet(int spriteRow, boolean isMirror, double rescale) {
        this.drawFromSheet(spriteRow, isMirror, this._spriteNameAndExtension, rescale);
    }

    public ImageIcon getImageIconFromSheet(int spriteRow) {
        return null;
    }

    public void drawExistingSprite(int spriteRow, boolean isMirror) {
        this._spriteRow = spriteRow;
        this._isMirror = isMirror;
        this.setIcon(this._isMirror ? this._sheetMirror[this._spriteRow] : this._sheet[this._spriteRow]);
        this.update();
    }

    public void drawExistingSprite(int spriteRow) {
        this._spriteRow = spriteRow;
        this.setIcon(this._sheet[this._spriteRow]);
        this.update();
    }

    public void setupSpriteSheet(int rows, int columns, int emptyPixels, int width, int height) {
        this._sheetRows = rows;
        this._sheetColumns = columns;
        this._emptyPixels = emptyPixels;
        this._sheetWidth = width;
        this._sheetHeight = height;
        this._altSheets.put(ViewUtil.trimDirectory(this._spriteNameAndExtension), new SheetDetail(width, height, rows, columns, emptyPixels));
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public void saveSheetColumn(int spriteNum, boolean saveMirror) {
        int rowInc = 0;
        int a = 0;
        this._sheet = new ImageIcon[this._sheetRows];
        if (saveMirror) {
            this._sheetMirror = new ImageIcon[this._sheetRows];
        }
        int locX = this._emptyPixels * (spriteNum / this._sheetRows + 1) + this._width * (spriteNum / this._sheetRows);
        BufferedImage spriteBuff = null;
        try {
            spriteBuff = ViewUtil.getResource(this._firstLoc, this._secondLoc, this._spriteNameAndExtension);
        }
        catch (IllegalArgumentException e) {
            System.out.println(this._spriteNameAndExtension);
        }
        catch (Exception e) {
            System.out.println(this._spriteNameAndExtension);
            e.printStackTrace();
        }
        while (rowInc < this._sheetRows) {
            int locY = this._emptyPixels * (rowInc + 1) + this._height * rowInc;
            try {
                if (!saveMirror) {
                    // empty if block
                }
            }
            catch (Exception e) {
                e.printStackTrace();
            }
            ++rowInc;
            ++a;
        }
        return;
    }

    @Override
    public void dispose() {
        this._sheet = null;
        super.dispose();
    }
}

