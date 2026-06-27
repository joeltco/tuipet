/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.Utility;
import View.ViewUtil;
import java.awt.Component;
import java.awt.Container;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.util.ArrayList;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;

public class SpriteObj
extends JLabel {
    private Icon[] _spriteSheet;
    private Icon[] _spriteSheetMirror;
    private ArrayList<ImageIcon> _altSprites = new ArrayList();
    private boolean _isMirror;
    private int _spriteNum;
    private String _spriteLoc;
    private Container _pane;
    private byte _scale;
    private int _sheetRows;
    private int _sheetColumns;
    private boolean _isEnabled;

    public Icon[] getSpriteSheet() {
        return this._spriteSheet;
    }

    public void setSpriteSheet(Icon[] sheet) {
        this._spriteSheet = sheet;
    }

    public void setSpriteSheetMirror(Icon[] sheet) {
        this._spriteSheetMirror = sheet;
    }

    public Icon[] getSpriteSheetMirror() {
        return this._spriteSheetMirror;
    }

    public ArrayList<ImageIcon> getAltSprites() {
        return this._altSprites;
    }

    public ImageIcon getAltSprite(String name) {
        return this._altSprites.get(this.getAltSpriteIndex(name));
    }

    private int getAltSpriteIndex(String s) {
        for (int i = 0; i < this._altSprites.size(); ++i) {
            if (!this._altSprites.get(i).getDescription().equals(s)) continue;
            return i;
        }
        return -1;
    }

    public boolean getIsMirror() {
        return this._isMirror;
    }

    public void setIsMirror(boolean newMirror) {
        this._isMirror = newMirror;
    }

    public int getSpriteNum() {
        return this._spriteNum;
    }

    public void setSpriteNum(int newNum) {
        this._spriteNum = newNum;
    }

    public String getSpriteLoc() {
        return this._spriteLoc;
    }

    public void setSpriteLoc(String newSpriteLoc) {
        this._spriteLoc = newSpriteLoc;
    }

    public Component getPane() {
        return this._pane;
    }

    public void setPane(JFrame newPane) {
        this._pane = newPane;
    }

    public int getSizeX() {
        return this.getWidth();
    }

    public void setSizeX(int newSizeX) {
        this.setSize(newSizeX, this.getHeight() / this._scale);
    }

    public int getSizeY() {
        return this.getHeight();
    }

    public void setSizeY(int newSizeY) {
        this.setSize(this.getWidth() / this._scale, newSizeY);
    }

    @Override
    public void setSize(int width, int height) {
        super.setSize(width * this._scale, height * this._scale);
    }

    public int getLocX() {
        return this.getX();
    }

    public void setLocX(int newLocX) {
        this.setLocation(newLocX * this._scale, this.getY());
    }

    public void setLocX(double newLocX) {
        this.setLocation((int)(newLocX * (double)this._scale), this.getY());
    }

    public int getLocY() {
        return this.getY();
    }

    public void setLocY(int newLocY) {
        this.setLocation(this.getX(), newLocY * this._scale);
    }

    public void setLocY(double newLocY) {
        this.setLocation(this.getX(), (int)(newLocY * (double)this._scale));
    }

    public int getSheetRows() {
        return this._sheetRows;
    }

    public int getColumnRows() {
        return this._sheetColumns;
    }

    public void setScale(int newScale) {
        this._scale = (byte)newScale;
    }

    public boolean getIsEnabled() {
        return this._isEnabled;
    }

    public void setIsEnabled(boolean b) {
        this._isEnabled = b;
    }

    public SpriteObj() {
    }

    public SpriteObj(String firstLoc, String secondLoc, String fileName, JPanel pane, int spriteSizeX, int spriteSizeY, int emptyPixels, byte scale, int sheetScale) {
        this.setupSpriteObj(firstLoc, secondLoc, fileName, pane, scale);
        this._spriteSheet = ViewUtil.divideSpriteSheet(this._spriteLoc, emptyPixels, spriteSizeX, spriteSizeY, sheetScale);
        this.setSize(spriteSizeX, spriteSizeY);
    }

    public SpriteObj(String firstLoc, String secondLoc, String fileName, JPanel pane, int spriteSizeX, int spriteSizeY, int emptyPixels, byte scale) {
        this(firstLoc, secondLoc, fileName, pane, spriteSizeX, spriteSizeY, emptyPixels, scale, scale);
    }

    public SpriteObj(String firstLoc, String secondLoc, String fileName, JPanel pane, int spriteSizeX, int spriteSizeY, byte scale) {
        this.setupSpriteObj(firstLoc, secondLoc, fileName, pane, scale);
        int x = spriteSizeX;
        int y = spriteSizeY;
        if (!this._spriteLoc.equals("")) {
            Icon i = this.addAltSprite(firstLoc, secondLoc, fileName);
            this.setIcon(i);
            x = spriteSizeX > 0 ? spriteSizeX : i.getIconWidth() / this._scale;
            y = spriteSizeY > 0 ? spriteSizeY : i.getIconHeight() / this._scale;
        }
        this.setSize(x, y);
    }

    public SpriteObj(String firstLoc, String secondLoc, String fileName, JPanel pane, byte scale) {
        this(firstLoc, secondLoc, fileName, pane, 0, 0, scale);
    }

    public SpriteObj(Icon image, JPanel pane, int locX, int locY, byte scale) {
        this._scale = scale;
        this.setSize(image.getIconWidth() / scale, image.getIconHeight() / scale);
        this._pane = pane;
        this.setIcon(image);
        if (this._pane != null) {
            this._pane.add(this);
        }
        this.setLocation(locX * this._scale, locY * this._scale);
    }

    @Override
    protected void paintComponent(Graphics g) {
        Graphics2D g2 = (Graphics2D)g;
        g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_OFF);
        super.paintComponent(g2);
    }

    private void setupSpriteObj(String firstLoc, String secondLoc, String fileName, JPanel pane, byte scale) {
        this._scale = scale;
        this._pane = pane;
        this._spriteLoc = Utility.getExistingFileLoc(firstLoc, secondLoc, fileName);
        super.setVisible(true);
        if (this._pane != null) {
            this._pane.add(this);
        }
    }

    public void setLoc(int x, int y) {
        this.setLocation(x * this._scale, y * this._scale);
    }

    public void setRawLoc(int x, int y) {
        this.setLocation(x, y);
    }

    public void removeIcon() {
        if (this.getIcon() != null) {
            this.setIcon(null);
        }
    }

    public void setIcon(String firstLoc, String secondLoc, String fileName, double scale) {
        Icon sprite = ViewUtil.resizeImage(new ImageIcon(ViewUtil.getResource(firstLoc, secondLoc, fileName)), scale);
        super.setIcon(sprite);
    }

    public void setIcon(String firstLoc, String secondLoc, String fileName) {
        this.setIcon(firstLoc, secondLoc, fileName, 1.0);
    }

    public void setAltIcon(String name) {
        for (int i = 0; i < this._altSprites.size(); ++i) {
            ImageIcon ii = this._altSprites.get(i);
            if (ii == null || !ii.getDescription().equals(name)) continue;
            this.setIcon(ii);
            break;
        }
    }

    public void setAltIcon(int i) {
        Icon icon = null;
        if (i < this._altSprites.size()) {
            icon = this._altSprites.get(i);
        }
        this.setIcon(icon);
    }

    public String getCurrentAltIcon() {
        ImageIcon i = (ImageIcon)this.getIcon();
        return i.getDescription();
    }

    public String trimDirectory(String loc) {
        char[] resource = loc.toCharArray();
        String name = "";
        for (int i = 0; i < resource.length && resource[i] != '.'; ++i) {
            name = name + resource[i];
        }
        return name;
    }

    public Icon addAltSprite(String firstLoc, String secondLoc, String fileName) {
        ImageIcon newIcon = (ImageIcon)ViewUtil.resizeImage(ViewUtil.getResource(firstLoc, secondLoc, fileName), (double)this._scale);
        newIcon.setDescription(this.trimDirectory(fileName));
        this._altSprites.add(newIcon);
        return newIcon;
    }

    public void addAltSprite(Icon image, String name) {
        ImageIcon ii = (ImageIcon)image;
        ii.setDescription(this.trimDirectory(name));
        this._altSprites.add(ii);
    }

    public void replaceAltSprite(String name, Icon image, String newName) {
        int i = this.getAltSpriteIndex(name);
        this._altSprites.remove(i);
        ImageIcon newImage = (ImageIcon)image;
        newImage.setDescription(newName);
        this._altSprites.add(newImage);
    }

    public void replaceAltSprite(String name, Icon image) {
        this.replaceAltSprite(name, image, name);
    }

    private void drawFromSheet() {
        this.drawFromSheet(this.isVisible());
    }

    private void drawFromSheet(boolean visible) {
        this.setVisible(visible);
        if (visible && this._spriteSheet != null) {
            try {
                if (this._isMirror) {
                    if (this._spriteSheetMirror != null) {
                        if (this._spriteNum < this._spriteSheetMirror.length) {
                            this.setIcon(this._spriteSheetMirror[this._spriteNum]);
                        } else {
                            this.setIcon(this._spriteSheetMirror[0]);
                        }
                    } else if (this._spriteNum < this._spriteSheet.length) {
                        this.setIcon(ViewUtil.flipIcon(this._spriteSheet[this._spriteNum]));
                    } else {
                        this.setIcon(ViewUtil.flipIcon(this._spriteSheet[0]));
                    }
                } else if (!this._isMirror) {
                    if (this._spriteNum < this._spriteSheet.length) {
                        this.setIcon(this._spriteSheet[this._spriteNum]);
                    } else {
                        this.setIcon(this._spriteSheet[0]);
                    }
                }
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public void moveLeft(int pixels) {
        this.setLocation(this.getX() - pixels * this._scale, this.getY());
    }

    public void moveRight(int pixels) {
        this.setLocation(this.getX() + pixels * this._scale, this.getY());
    }

    public void moveUp(int pixels) {
        this.setLocation(this.getX(), this.getY() - pixels * this._scale);
    }

    public void moveDown(int pixels) {
        this.setLocation(this.getX(), this.getY() + pixels * this._scale);
    }

    private void setNumMirror(int spriteNum, boolean isMirror) {
        if (this._spriteSheet != null) {
            this._isMirror = isMirror;
            this._spriteNum = spriteNum;
        }
    }

    public void drawNum(int n) {
        this.drawNumMirror(n, this._isMirror);
    }

    public void drawNumMirror(int n, boolean m, boolean v) {
        this.setNumMirror(n, m);
        this.drawFromSheet(v);
    }

    public void drawNumMirror(int n, boolean m) {
        this.setNumMirror(n, m);
        this.drawFromSheet(true);
    }

    public void saveSpriteMirror() {
        this._spriteSheetMirror = new Icon[this._spriteSheet.length];
        for (int i = 0; i < this._spriteSheet.length; ++i) {
            this._spriteSheetMirror[i] = ViewUtil.flipIcon(this._spriteSheet[i]);
        }
    }

    public void dispose() {
        this._altSprites = null;
        this._spriteLoc = null;
        if (this._spriteSheet != null) {
            for (Icon i : this._spriteSheet) {
                if (i == null) continue;
                i = null;
            }
        }
        this._spriteSheet = null;
        if (this._spriteSheetMirror != null) {
            for (Icon i : this._spriteSheetMirror) {
                if (i == null) continue;
                i = null;
            }
        }
        this._spriteSheetMirror = null;
        if (this._altSprites != null) {
            this._altSprites.clear();
        }
        this._altSprites = null;
        if (this._pane != null) {
            this._pane.remove(this);
            this._pane = null;
        }
    }
}

