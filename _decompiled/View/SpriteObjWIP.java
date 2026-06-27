/*
 * Decompiled with CFR 0.152.
 */
package View;

import Model.ViewSettings;
import View.SpriteDetail;
import View.ViewUtil;
import java.util.HashMap;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JLabel;
import javax.swing.JPanel;

public class SpriteObjWIP
extends JLabel {
    protected boolean _isMirror;
    protected SpriteDetail _currentAltSprite;
    protected String _firstLoc;
    protected String _secondLoc;
    protected String _spriteNameAndExtension;
    protected JPanel _pane;
    protected ViewSettings _view;
    protected double _spriteRescale;
    protected int _width;
    protected int _height;
    protected int _x;
    protected int _y;
    protected float _opacity = 1.0f;
    protected final HashMap<String, SpriteDetail> _altSprites = new HashMap();
    protected boolean _canInteract = true;

    public boolean isMirror() {
        return this._isMirror;
    }

    public void setMirror(boolean newMirror) {
        this._isMirror = newMirror;
    }

    public String getSpriteLoc() {
        return this._spriteNameAndExtension;
    }

    public void setSpriteLoc(String newSpriteLoc) {
        this._spriteNameAndExtension = newSpriteLoc;
    }

    public SpriteDetail getCurrentAltSprite() {
        return this._currentAltSprite;
    }

    public HashMap<String, SpriteDetail> getAltSprites() {
        return this._altSprites;
    }

    public JPanel getPane() {
        return this._pane;
    }

    public void setPane(JPanel newPane) {
        this._pane = newPane;
    }

    @Override
    public int getWidth() {
        return this._width;
    }

    public void setWidth(int newSizeX) {
        this._width = newSizeX;
    }

    @Override
    public int getHeight() {
        return this._height;
    }

    public void setHeight(int newSizeY) {
        this._height = newSizeY;
    }

    @Override
    public int getX() {
        return this._x;
    }

    public void setX(int newLocX) {
        this._x = newLocX;
    }

    @Override
    public int getY() {
        return this._y;
    }

    public void setY(int newLocY) {
        this._y = newLocY;
    }

    public void setSpriteRescale(double s) {
        this._spriteRescale = s;
    }

    public boolean canInteract() {
        return this._canInteract;
    }

    public void setCanInteract(boolean b) {
        this._canInteract = b;
    }

    public SpriteObjWIP(String firstLoc, String secondLoc, String fileNameAndExtension, JPanel pane, int spriteWidth, int spriteHeight, ViewSettings view) {
        this(firstLoc, secondLoc, fileNameAndExtension, pane, spriteWidth, spriteHeight, view, view.getGameScale());
    }

    public SpriteObjWIP(String firstLoc, String secondLoc, String fileNameAndExtension, JPanel pane, int spriteWidth, int spriteHeight, ViewSettings view, double spriteRescale) {
        this._firstLoc = firstLoc;
        this._secondLoc = secondLoc;
        this._view = view;
        this._spriteRescale = spriteRescale;
        this._pane = pane;
        if (!fileNameAndExtension.isEmpty()) {
            this._altSprites.put(ViewUtil.trimDirectory(fileNameAndExtension), new SpriteDetail(fileNameAndExtension, this._opacity, this._spriteRescale, false, spriteWidth, spriteHeight, this._view));
        }
        this._spriteNameAndExtension = fileNameAndExtension;
        this._width = spriteWidth;
        this._height = spriteHeight;
        this.setSize(this._width, this._height);
        super.setVisible(true);
        if (this._pane != null) {
            this._pane.add(this);
        }
        this.update();
    }

    public void addAltSprite(String name, String location, float opacity, double spriteRescale, int width, int height) {
        this._altSprites.put(name, new SpriteDetail(location, opacity, spriteRescale, false, width, height, this._view));
    }

    public void addAltSprite(String location, int width, int height) {
        this._altSprites.put(ViewUtil.trimDirectory(location), new SpriteDetail(location, this._opacity, 1.0, false, width, height, this._view));
    }

    public void addAltSprite(String name, String location, float opacity, double spriteRescale, boolean isMirror, int width, int height) {
        this._altSprites.put(name, new SpriteDetail(location, opacity, spriteRescale, isMirror, width, height, this._view));
    }

    public void setAltSprite(String name) {
        SpriteDetail s;
        this._currentAltSprite = s = this._altSprites.get(name);
        this._spriteNameAndExtension = s.getLocation();
        this._opacity = s.getOpacity();
        this._spriteRescale = s.getSpriteRescale();
        this._isMirror = s.isMirror();
        this._width = s.getWidth();
        this._height = s.getHeight();
    }

    public void setLoc(int x, int y) {
        this._x = x;
        this._y = y;
    }

    @Override
    public void setSize(int x, int y) {
        this._width = x;
        this._height = y;
    }

    protected void setIcon(ImageIcon icon) {
        this.setIcon(icon, this._spriteRescale);
    }

    protected void setIcon(Icon icon, double rescale) {
        if (icon != null) {
            if (this._isMirror) {
                // empty if block
            }
            if (this._opacity < 1.0f) {
                icon = ViewUtil.getTransparentImage(icon, this._opacity);
            }
        }
        this.update();
        super.setIcon(this._view.getGameScale() != 1.0 || rescale != 1.0 ? ViewUtil.resizeImage(icon, rescale * this._view.getGameScale()) : icon);
    }

    public void removeIcon() {
        this.setIcon(null);
    }

    public void drawAltSprite(String name) {
        this.setAltSprite(name);
        this.draw();
    }

    public void draw(String fileNameAndExtension, double rescale) {
        this.setIcon(ViewUtil.getResourceAsImageIcon(this._firstLoc, this._secondLoc, fileNameAndExtension), rescale);
    }

    public void draw(String fileNameAndExtension) {
        this.draw(fileNameAndExtension, this._spriteRescale);
    }

    public void draw(double rescale) {
        this.setIcon(ViewUtil.getResourceAsImageIcon(this._firstLoc, this._secondLoc, this._spriteNameAndExtension), rescale);
    }

    public void draw() {
        this.draw(this._spriteRescale);
    }

    public void draw(boolean v) {
        this.draw();
        this.update(v);
    }

    public void draw(boolean v, double rescale) {
        this.draw(rescale);
        this.update(v);
    }

    public void update() {
        super.setBounds((int)((double)this._x * this._view.getGameScale()), (int)((double)this._y * this._view.getGameScale()), (int)((double)this._width * this._view.getGameScale()), (int)((double)this._height * this._view.getGameScale()));
    }

    public void update(boolean visible) {
        this.update();
        super.setVisible(visible);
    }

    public void moveLeft(int pixels) {
        this._x -= pixels;
    }

    public void moveRight(int pixels) {
        this._x += pixels;
    }

    public void moveUp(int pixels) {
        this._y -= pixels;
    }

    public void moveDown(int pixels) {
        this._y += pixels;
    }

    public void dispose() {
        this._spriteNameAndExtension = null;
        this.setIcon(null);
        this._pane.remove(this);
        this._pane = null;
    }
}

