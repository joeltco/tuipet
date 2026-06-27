/*
 * Decompiled with CFR 0.152.
 */
package View;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import javax.swing.JPanel;

public class Polygon
extends JPanel {
    private int _width;
    private int _height;
    private int _red;
    private int _green;
    private int _blue;
    private int _alpha;
    private Color _color;

    public void setWidth(int width) {
        this._width = width;
        this.setBounds(this.getX(), this.getY(), this._width, this._height);
    }

    public void setHeight(int height) {
        this._height = height;
        this.setBounds(this.getX(), this.getY(), this._width, this._height);
    }

    public int getAlpha() {
        return this._alpha;
    }

    public int getRed() {
        return this._red;
    }

    public int getBlue() {
        return this._blue;
    }

    public Polygon(int width, int height, int red, int green, int blue, int alpha) {
        this.setOpaque(false);
        this._width = width;
        this._height = height;
        this.setBounds(0, 0, this._width, this._height);
        this._alpha = alpha;
        this._red = red;
        this._green = green;
        this._blue = blue;
        this._color = new Color(this._red, this._green, this._blue, this._alpha);
    }

    public Polygon(int width, int height, String hex, int alpha) {
        this.setOpaque(false);
        this._color = Color.decode(hex);
        this._color = new Color(this._color.getRed(), this._color.getGreen(), this._color.getBlue(), alpha);
        this._width = width;
        this._height = height;
        this.setBounds(0, 0, this._width, this._height);
        this._alpha = this._color.getAlpha();
        this._red = this._color.getRed();
        this._green = this._color.getGreen();
        this._blue = this._color.getBlue();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D)g.create();
        g2.setColor(this._color);
        g2.fillRect(0, 0, this._width, this._height);
        g2.dispose();
    }

    public void changeColor(int red, int green, int blue, int alpha) {
        this._alpha = alpha;
        this._red = red;
        this._green = green;
        this._blue = blue;
        this._color = new Color(this._red, this._green, this._blue, this._alpha);
        this.repaint();
    }
}

