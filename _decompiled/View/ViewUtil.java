/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.Utility;
import Model.Consumable;
import Model.Enum;
import Model.PhysicalState;
import View.SpriteObj;
import View.ViewConfig;
import java.awt.AlphaComposite;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.Toolkit;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Paths;
import javax.imageio.ImageIO;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JFrame;

public class ViewUtil {
    public static final Color TRANSPARENT_BLACK = new Color(0, 0, 0, 1);
    public static final Enum.Menu[] SHOP = new Enum.Menu[]{Enum.Menu.Food_Inventory_Sell, Enum.Menu.Item_Inventory_Sell, Enum.Menu.Sell_Nutrition, Enum.Menu.Item_Purchase, Enum.Menu.Habitat_Purchase, Enum.Menu.Item_Sale, Enum.Menu.Food_Sale, Enum.Menu.Buy_Item, Enum.Menu.Buy_Nutrition, Enum.Menu.Buy_Food, Enum.Menu.Food_Purchase, Enum.Menu.Food_Shop, Enum.Menu.Card_Shop, Enum.Menu.Item_Shop, Enum.Menu.Shop_Validation, Enum.Menu.Food_Buy_Sell_Validation, Enum.Menu.Item_Buy_Sell_Validation};
    public static final Enum.Menu[] FIRST_AID = new Enum.Menu[]{Enum.Menu.Med_Nutrition, Enum.Menu.Medical, Enum.Menu.Use_Med_Food, Enum.Menu.Use_Med_Item};
    public static final Enum.Menu[] DIGICORE = new Enum.Menu[]{Enum.Menu.EvolSilhouette, Enum.Menu.EvolutionState};
    public static final Enum.Menu[] HABITAT_VALIDATION = new Enum.Menu[]{Enum.Menu.Habitat_Compatibility, Enum.Menu.Habitat_Description, Enum.Menu.Habitat_Incompatibility, Enum.Menu.Habitat_Inventory, Enum.Menu.Habitat_Shop, Enum.Menu.Habitat_Shop_Compatibility, Enum.Menu.Habitat_Shop_Description, Enum.Menu.Habitat_Shop_Incompatibility};
    public static final Enum.State[] TRANSACTION_ANIM = new Enum.State[]{Enum.State.Buying_Food, Enum.State.Buying_Item, Enum.State.Buying_Habitat, Enum.State.Selling_Food, Enum.State.Selling_Item};
    public static final Enum.State[] DIGICORE_ANIM = new Enum.State[]{Enum.State.EvolSilhouetteBack, Enum.State.EvolSilhouetteTransition};
    public static final Enum.Menu[] REMOVE_HIGHLIGHT = new Enum.Menu[]{Enum.Menu.None, Enum.Menu.EvolutionState, Enum.Menu.EvolSilhouette, Enum.Menu.Start, Enum.Menu.Set_EggClock, Enum.Menu.Save_Name, Enum.Menu.Load_Name, Enum.Menu.SetDifficulty, Enum.Menu.Host_Name_Battle, Enum.Menu.Host_Name_Jogress, Enum.Menu.Settings, Enum.Menu.Host_Port_Battle, Enum.Menu.Host_Port_Jogress};

    public static void setBackgroundColor(JFrame f, float alpha) {
        Color color;
        try {
            Field field = Class.forName("java.awt.Color").getField(ViewConfig._backgroundColor);
            color = (Color)field.get(null);
            color = new Color((float)color.getRed(), (float)color.getGreen(), (float)color.getBlue(), alpha);
        }
        catch (Exception e) {
            color = new Color(1.0f, 1.0f, 1.0f, alpha);
        }
        f.getContentPane().setBackground(color);
        f.setBackground(color);
    }

    public static URL getURLResource(Class<?> c, String firstLoc, String secondLoc, String fileName) {
        File f = new File(firstLoc + fileName);
        URL url = null;
        if (f.exists()) {
            try {
                url = f.toURI().toURL();
            }
            catch (Exception e) {
                url = c.getResource(firstLoc + fileName);
            }
        } else {
            url = c.getResource(secondLoc + fileName);
        }
        return url;
    }

    public static Icon getResource(String path) {
        InputStream is = null;
        ImageIcon i = null;
        try {
            try {
                is = Files.newInputStream(Paths.get(path, new String[0]), new OpenOption[0]);
            }
            catch (Exception e) {
                is = ViewUtil.class.getResourceAsStream(path);
            }
            i = new ImageIcon(ImageIO.read(is));
        }
        catch (IOException ex) {
            ex.printStackTrace();
        }
        return i;
    }

    public static Icon[] getConsumableSheet(String firstLoc, String secondLoc, String name, Consumable c, int emptyPixels, int width, int height, double scale) {
        String spriteName = Utility.getExistingFileLoc(firstLoc, secondLoc, "sprites" + name + c.getSpriteSet() + ".png");
        return ViewUtil.divideIntoColumn(spriteName, emptyPixels, c.getSpriteNum(), width, height, scale);
    }

    public static void setConsumableSet(String firstLoc, String secondLoc, String name, Consumable c, SpriteObj o, int emptyPixels, int width, int height, double scale) {
        o.setSpriteSheet(ViewUtil.getConsumableSheet(firstLoc, secondLoc, name, c, emptyPixels, width, height, scale));
    }

    public static ImageIcon getResourceAsImageIcon(String MOD_FOLDER, String RESOURCES_FOLDER, String fileName) {
        return new ImageIcon(ViewUtil.getResource(MOD_FOLDER, RESOURCES_FOLDER, fileName));
    }

    public static BufferedImage getResource(String MOD_FOLDER, String RESOURCES_FOLDER, String fileName) {
        InputStream is = Utility.getInputStream(MOD_FOLDER, RESOURCES_FOLDER, fileName);
        BufferedImage i = null;
        try {
            if (is != null) {
                i = ImageIO.read(is);
            }
        }
        catch (IOException ex) {
            ex.printStackTrace();
        }
        return i;
    }

    public static void centerMain(Component c) {
        Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
        c.setLocation(dim.width / 2 - c.getWidth() / 2, dim.height / 2 - c.getHeight() / 2);
    }

    public static void centerObj(Component base, Component obj) {
        boolean isParent = base == obj.getParent();
        int x = (isParent ? 0 : base.getX()) + base.getWidth() / 2 - obj.getWidth() / 2;
        int y = (isParent ? 0 : base.getY()) + base.getHeight() / 2 - obj.getHeight() / 2;
        obj.setLocation(x, y);
    }

    public static int[] centerObj(Component base, Icon obj, int scale, int pixelUnit) {
        int x = base.getX() / scale + (base.getWidth() / scale / 2 - obj.getIconWidth() / scale / 2) / pixelUnit * pixelUnit;
        int y = base.getY() / scale + (base.getHeight() / scale / 2 - obj.getIconHeight() / scale / 2) / pixelUnit * pixelUnit;
        return new int[]{x, y};
    }

    public static String trimDirectory(String loc) {
        char[] resource = loc.toCharArray();
        String name = "";
        for (int i = 0; i < resource.length && resource[i] != '.'; ++i) {
            name = resource[i] == '/' ? "" : name + resource[i];
        }
        return name;
    }

    public static Icon cropImage(Icon icon, int width, int height) {
        BufferedImage buff = ViewUtil.createBuffImage(icon);
        return new ImageIcon(buff.getSubimage(0, 0, width, height));
    }

    public static Icon[] divideIntoColumn(String loc, int emptyPixels, int spriteNum, int width, int height, double scale) {
        Icon[] spriteSheet = null;
        int rowInc = 0;
        int a = 0;
        int rows = 0;
        int columns = 0;
        int locX = 0;
        BufferedImage spriteBuff = null;
        try {
            spriteBuff = ViewUtil.createBuffImage(ViewUtil.getResource(loc));
            int[] d = ViewUtil.calcNumSpritesInSheet(spriteBuff.getWidth(), spriteBuff.getHeight(), width, height, emptyPixels);
            rows = d[0];
            columns = d[1];
            spriteSheet = new Icon[rows];
            locX = emptyPixels * (spriteNum / rows + 1) + width * (spriteNum / rows);
        }
        catch (IllegalArgumentException e) {
            System.out.println(e.getMessage() + ":" + loc);
            e.printStackTrace();
        }
        catch (Exception e) {
            System.out.println(loc);
            e.printStackTrace();
        }
        if (spriteSheet != null) {
            while (rowInc < rows) {
                int locY = emptyPixels * (rowInc + 1) + height * rowInc;
                try {
                    spriteSheet[a] = ViewUtil.resizeImage(spriteBuff.getSubimage(locX, locY, width, height), scale);
                }
                catch (Exception e) {
                    e.printStackTrace();
                }
                ++rowInc;
                ++a;
            }
        }
        return spriteSheet;
    }

    public static int[] calcNumSpritesInSheet(int sheetWidth, int sheetHeight, int spriteWidth, int spriteHeight, int emptyPixels) {
        int rows = (int)((double)sheetHeight / (double)(spriteHeight + emptyPixels));
        int columns = (int)((double)sheetWidth / (double)(spriteWidth + emptyPixels));
        return new int[]{rows, columns};
    }

    public static Icon[] divideSpriteSheet(String loc, int emptyPixels, int width, int height, int scale) {
        int rows = 0;
        int columns = 0;
        int rowInc = 0;
        int a = 0;
        Icon[] spriteSheet = null;
        BufferedImage spriteBuff = null;
        try {
            spriteBuff = ViewUtil.createBuffImage(ViewUtil.getResource(loc));
            int[] d = ViewUtil.calcNumSpritesInSheet(spriteBuff.getWidth(), spriteBuff.getHeight(), width, height, emptyPixels);
            rows = d[0];
            columns = d[1];
            spriteSheet = new Icon[rows * columns];
        }
        catch (IllegalArgumentException e) {
            System.out.println(e.getMessage() + ":" + loc);
            e.printStackTrace();
        }
        catch (Exception e) {
            System.out.println(loc);
            e.printStackTrace();
        }
        if (spriteSheet != null) {
            for (int i = 0; i < columns; ++i) {
                while (rowInc < rows) {
                    int locX = emptyPixels * (i + 1) + width * i;
                    int locY = emptyPixels * (rowInc + 1) + height * rowInc;
                    try {
                        spriteSheet[a] = ViewUtil.resizeImage(spriteBuff.getSubimage(locX, locY, width, height), (double)scale);
                    }
                    catch (Exception e) {
                        e.printStackTrace();
                    }
                    ++rowInc;
                    ++a;
                }
                rowInc = 0;
            }
        }
        return spriteSheet;
    }

    public static Icon getIndividualIcon(String firstLoc, String secondLoc, String fileName, double scale, int spriteNum, int row, int width, int height, int emptyPixels) {
        BufferedImage spriteBuff = ViewUtil.getResource(firstLoc, secondLoc, fileName);
        int totalRows = ViewUtil.calcNumSpritesInSheet(spriteBuff.getWidth(), spriteBuff.getHeight(), width, height, emptyPixels)[0];
        int locX = emptyPixels * (spriteNum / totalRows + 1) + width * (spriteNum / totalRows);
        int locY = emptyPixels * (row + 1) + height * row;
        return ViewUtil.resizeImage(spriteBuff.getSubimage(locX, locY, width, height), scale);
    }

    private static BufferedImage createTransformed(Icon image, AffineTransform at) {
        BufferedImage newImage = new BufferedImage(image.getIconWidth(), image.getIconHeight(), 2);
        Graphics2D g = newImage.createGraphics();
        g.transform(at);
        ImageIcon ii = (ImageIcon)image;
        g.drawImage(ii.getImage(), 0, 0, null);
        g.dispose();
        return newImage;
    }

    private static BufferedImage rotate(Icon source, int rotationAngle) {
        BufferedImage src = ViewUtil.createBuffImage(source);
        double theta = Math.PI / 180 * (double)rotationAngle;
        int width = src.getWidth();
        int height = src.getHeight();
        BufferedImage dest = rotationAngle == 90 || rotationAngle == 270 ? new BufferedImage(src.getHeight(), src.getWidth(), src.getType()) : new BufferedImage(src.getWidth(), src.getHeight(), src.getType());
        Graphics2D graphics2D = dest.createGraphics();
        switch (rotationAngle) {
            case 90: {
                graphics2D.translate((height - width) / 2, (height - width) / 2);
                graphics2D.rotate(theta, height / 2, width / 2);
                break;
            }
            case 270: {
                graphics2D.translate((width - height) / 2, (width - height) / 2);
                graphics2D.rotate(theta, height / 2, width / 2);
                break;
            }
            default: {
                graphics2D.translate(0, 0);
                graphics2D.rotate(theta, width / 2, height / 2);
            }
        }
        graphics2D.drawRenderedImage(src, null);
        return dest;
    }

    private static BufferedImage rotateCounterClockwise90(Icon source) {
        return ViewUtil.rotate(source, 270);
    }

    public static Icon flipHorizontally(Icon image) {
        AffineTransform at = new AffineTransform();
        at.concatenate(AffineTransform.getScaleInstance(-1.0, 1.0));
        at.concatenate(AffineTransform.getTranslateInstance(-image.getIconWidth(), 0.0));
        return new ImageIcon(ViewUtil.createTransformed(image, at));
    }

    public static ImageIcon flipVertically(Icon image) {
        AffineTransform at = new AffineTransform();
        at.concatenate(AffineTransform.getScaleInstance(1.0, -1.0));
        at.concatenate(AffineTransform.getTranslateInstance(0.0, -image.getIconHeight()));
        return new ImageIcon(ViewUtil.createTransformed(image, at));
    }

    public static Icon getRotatedIcon(int rotations, Icon i) {
        switch (rotations) {
            case 1: {
                return new ImageIcon(ViewUtil.rotate(i, 90));
            }
            case 2: {
                return new ImageIcon(ViewUtil.rotate(i, 180));
            }
            case 3: {
                return new ImageIcon(ViewUtil.rotate(i, 270));
            }
        }
        return i;
    }

    public static BufferedImage createBuffImage(Icon image, double rescale) {
        Icon r = ViewUtil.resizeImage(image, rescale);
        return ViewUtil.createBuffImage(r);
    }

    public static BufferedImage createBuffImage(Icon image) {
        BufferedImage newImage = new BufferedImage(image.getIconWidth(), image.getIconHeight(), 2);
        Graphics2D g = newImage.createGraphics();
        image.paintIcon(null, g, 0, 0);
        g.dispose();
        return newImage;
    }

    static void floodFillUtil(int[][] screen, int x, int y, int prevC, int newC, int width, int height) {
        if (x < 0 || x >= width || y < 0 || y >= height) {
            return;
        }
        if (screen[x][y] != prevC) {
            return;
        }
        screen[x][y] = newC;
        ViewUtil.floodFillUtil(screen, x + 1, y, prevC, newC, width, height);
        ViewUtil.floodFillUtil(screen, x - 1, y, prevC, newC, width, height);
        ViewUtil.floodFillUtil(screen, x, y + 1, prevC, newC, width, height);
        ViewUtil.floodFillUtil(screen, x, y - 1, prevC, newC, width, height);
    }

    static void floodFill(int[][] screen, int x, int y, int newC, int width, int height) {
        int prevC = screen[x][y];
        if (prevC == newC) {
            return;
        }
        ViewUtil.floodFillUtil(screen, x, y, prevC, newC, width, height);
    }

    public static Icon getSilhouetteImage(Icon image) {
        int width = image.getIconWidth() + 2;
        int height = image.getIconHeight() + 2;
        BufferedImage b = new BufferedImage(width, height, 2);
        Graphics2D g = b.createGraphics();
        image.paintIcon(null, g, 1, 1);
        g.dispose();
        int black = new Color(0, 0, 0, 255).getRGB();
        int white = new Color(255, 255, 255, 255).getRGB();
        int[][] screen = new int[width][height];
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                screen[x][y] = x < width && y < height ? b.getRGB(x, y) : white;
            }
        }
        int x = 0;
        int y = 0;
        int newC = 2;
        ViewUtil.floodFill(screen, x, y, newC, width, height);
        for (y = 0; y < height; ++y) {
            for (x = 0; x < width; ++x) {
                if (screen[x][y] == newC || x >= width || y >= height) continue;
                b.setRGB(x, y, Color.BLACK.getRGB());
            }
        }
        ImageIcon i = new ImageIcon(b.getSubimage(1, 1, image.getIconWidth(), image.getIconHeight()));
        return i;
    }

    public static Icon getTransparentImage(Icon image, float opacity) {
        BufferedImage transp = new BufferedImage(image.getIconWidth(), image.getIconHeight(), 2);
        Graphics2D g = transp.createGraphics();
        g.setComposite(AlphaComposite.getInstance(3, opacity));
        image.paintIcon(null, g, 0, 0);
        g.dispose();
        return new ImageIcon(transp);
    }

    public static Icon resizeImage(BufferedImage image, int width, int height) {
        return new ImageIcon(image.getScaledInstance(width, height, 2));
    }

    public static Icon resizeImage(Icon image, int width, int height) {
        BufferedImage bi = ViewUtil.createBuffImage(image);
        return ViewUtil.resizeImage(bi, width, height);
    }

    public static Icon resizeImage(Icon image, double scale) {
        try {
            BufferedImage i = ViewUtil.createBuffImage(image);
            return ViewUtil.resizeImage(i, scale);
        }
        catch (Exception e) {
            e.printStackTrace();
            return image;
        }
    }

    public static Icon resizeImage(String firstLoc, String secondLoc, String fileName, double scale) {
        ImageIcon image = ViewUtil.getResourceAsImageIcon(firstLoc, secondLoc, fileName);
        return ViewUtil.resizeImage(image, scale);
    }

    public static Icon resizeImage(BufferedImage image, double scale) {
        try {
            Image tmp = image;
            if (scale != 1.0) {
                int width = (int)((double)image.getWidth() * scale);
                int height = (int)((double)image.getHeight() * scale);
                tmp = image.getScaledInstance(width, height, 2);
            }
            return new ImageIcon(tmp);
        }
        catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static BufferedImage trimImage(BufferedImage image, double widthCoefficient, double heightCoefficient, int pixelUnit, int minHeight, int maxHeight) {
        int left;
        int top;
        int width = image.getWidth();
        int height = image.getHeight();
        int bottom = top = height / 2;
        int right = left = width / 2;
        for (int x = 0; x < width; ++x) {
            for (int y = 0; y < height; ++y) {
                if (image.getRGB(x, y) == 0) continue;
                top = Math.min(top, y);
                bottom = Math.max(bottom, y);
                left = Math.min(left, x);
                right = Math.max(right, x);
            }
        }
        int newHeight = bottom - top + 1;
        int newWidth = right - left + 1;
        int h = (int)Math.ceil((double)(newHeight / pixelUnit) * heightCoefficient) * pixelUnit;
        int w = (int)Math.ceil((double)(newWidth / pixelUnit) * widthCoefficient) * pixelUnit;
        h = h < minHeight && minHeight < image.getHeight() ? minHeight : h;
        h = h > maxHeight && maxHeight < image.getHeight() ? maxHeight : h;
        return image.getSubimage(left, top, w, h);
    }

    public static String colorNumberAfterChar(char[] valid, String text, String color) {
        int loc = 0;
        if (valid != null) {
            char[] chars = text.toCharArray();
            for (int i = 0; i < chars.length; ++i) {
                for (char v : valid) {
                    if (chars[i] != v) continue;
                    loc = i + 1;
                    break;
                }
                if (loc > 0) break;
            }
        }
        String textToBeColored = text.substring(loc);
        text = text.replace("<", "&lt;");
        return "<html>" + text.replace(textToBeColored, "<font color='" + color + "'>" + textToBeColored + "</font>") + "</html>";
    }

    public static boolean containsMenu(Enum.Menu[] menus, Enum.Menu menu) {
        boolean contains = false;
        for (Enum.Menu m : menus) {
            if (m != menu) continue;
            contains = true;
            break;
        }
        return contains;
    }

    public static String getDigicoreBackground(PhysicalState digimon) {
        Enum.Field f = digimon.getDNA().getHighestDNA();
        if (f == Enum.Field.NA) {
            f = digimon.getField();
        }
        String background = "digicoreN.png";
        switch (f) {
            case None: {
                background = "digicoreN.png";
                break;
            }
            case DragonsRoar: {
                background = "digicoreDr.png";
                break;
            }
            case DeepSaver: {
                background = "digicoreDs.png";
                break;
            }
            case JungleTrooper: {
                background = "digicoreJt.png";
                break;
            }
            case MetalEmpire: {
                background = "digicoreMe.png";
                break;
            }
            case NatureSpirit: {
                background = "digicoreNsp.png";
                break;
            }
            case WindGuardian: {
                background = "digicoreWg.png";
                break;
            }
            case NightmareSoldier: {
                background = "digicoreNs.png";
                break;
            }
            case DarkArea: {
                background = "digicoreDa.png";
                break;
            }
            case VirusBuster: {
                background = "digicoreVb.png";
            }
        }
        return background;
    }

    private static BufferedImage createFlipped(Icon image) {
        AffineTransform at = new AffineTransform();
        at.concatenate(AffineTransform.getScaleInstance(-1.0, 1.0));
        at.concatenate(AffineTransform.getTranslateInstance(-image.getIconWidth(), 0.0));
        return ViewUtil.createTransformed(image, at);
    }

    private static BufferedImage createFlipRotate(Icon image) {
        AffineTransform at = new AffineTransform();
        at.concatenate(AffineTransform.getScaleInstance(-1.0, -1.0));
        at.concatenate(AffineTransform.getTranslateInstance(-image.getIconWidth(), -image.getIconWidth()));
        return ViewUtil.createTransformed(image, at);
    }

    public static Icon flipIcon(Icon image) {
        return new ImageIcon(ViewUtil.createFlipped(image));
    }

    public static Icon rotateIcon(Icon image) {
        return new ImageIcon(ViewUtil.createFlipRotate(image));
    }

    public static String getCenteredText(String text) {
        return "<html><p style=\"text-align:center\">" + text + "</p></html>";
    }

    public static Icon[] getFoodSheet(Consumable c, String firstLoc, String secondLoc, double scale) {
        Icon[] sheet = null;
        if (c != null) {
            sheet = ViewUtil.getConsumableSheet(firstLoc, secondLoc, "Food", c, 6, 24, 24, scale);
        }
        return sheet;
    }

    public static int getFoodGroupNum(Enum.Food f) {
        switch (f) {
            case Meat: {
                return 0;
            }
            case Veg: {
                return 3;
            }
            case Fruit: {
                return 2;
            }
            case Fish: {
                return 1;
            }
            case Med: {
                return 4;
            }
            case Junk: {
                return 6;
            }
            case Grain: {
                return 46;
            }
            case Dairy: {
                return 47;
            }
        }
        return -1;
    }
}

