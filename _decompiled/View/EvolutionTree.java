/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.ClockTic;
import Controller.Utility;
import Model.Config;
import Model.Consumable;
import Model.CrashEntry;
import Model.Enum;
import Model.Evolution;
import Model.EvolutionInfo;
import Model.Habitat;
import Model.JogressAttributePair;
import Model.PhysicalState;
import View.DisplayPane;
import View.JTextFieldLimit;
import View.KeyboardCursor;
import View.SoundConfig;
import View.SoundObj;
import View.SpriteObj;
import View.ViewConfig;
import View.ViewUtil;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.util.AbstractMap;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EventListener;
import java.util.Map;
import javax.swing.BorderFactory;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JTextField;

public class EvolutionTree
extends JFrame {
    private final String MOD_FOLDER;
    private final String RESOURCES_FOLDER;
    private byte _page;
    private PhysicalState _digimon;
    private ClockTic _controller;
    private KeyboardCursor _keyboard;
    private JTextField _searchBar;
    private SpriteObj _searchButton;
    private DisplayPane _display;
    private DisplayPane _back;
    private DisplayPane _dna;
    private DisplayPane _global;
    private JLabel _border = new JLabel();
    private Icon _locked;
    private Icon _null;
    private SpriteObj _evolutionTree;
    private int _posx;
    private int _posy;
    private SpriteObj _reqTab;
    private SpriteObj _bonusTab;
    private SpriteObj _jogressTab;
    private SpriteObj _closeButton;
    private SoundObj _sounds;
    private byte _scale;
    private double _reducedScale;
    private SpriteObj _upButton;
    private SpriteObj _downButton;
    private SpriteObj _historyDownButton;
    private SpriteObj _historyUpButton;
    private SpriteObj _leftButton;
    private SpriteObj _rightButton;
    private SpriteObj _jogressLeftButton;
    private SpriteObj _jogressRightButton;
    private byte _jogressPage;
    private SpriteObj _collapsedRightButton;
    private SpriteObj _currentDigimon;
    private EvolutionInfo _currentInfo;
    private SpriteObj[] _evolEvolutions;
    private SpriteObj[] _evolPreEvolutions;
    private int _preEvolutionsPage;
    private int _evolutionsPage;
    private SpriteObj _lastEvolButtonPressed;
    private EvolutionInfo _lastDigimon;
    private int _historyPage;
    private int _generationPage;
    private int _duplicatePage;
    private ArrayList<EvolutionInfo> _duplicates = new ArrayList();
    private int _collapsePage;
    private ArrayList<EvolutionInfo> _collapsed = new ArrayList();
    private SpriteObj _foodLabel;
    private SpriteObj _itemLabel;
    ArrayList<Habitat> _habitats;
    private SpriteObj _selectDigimon;
    private EvolutionInfo _selectInfo;
    private SpriteObj _name;
    private SpriteObj _specialEvol;
    private SpriteObj _fieldLabel;
    private SpriteObj _elementLabel;
    private SpriteObj _attributeLabel;
    private SpriteObj _vaccineReq;
    private SpriteObj _dataReq;
    private SpriteObj _virusReq;
    private SpriteObj _weightReq;
    private SpriteObj _mistakeReq;
    private SpriteObj _overeatReq;
    private SpriteObj _disturbReq;
    private SpriteObj _sickReq;
    private SpriteObj _injReq;
    private SpriteObj _battleReq;
    private SpriteObj _winReq;
    private SpriteObj _obedienceReq;
    private SpriteObj _timeReq;
    private SpriteObj _moodReq;
    private SpriteObj _tempReq;
    private SpriteObj _levelReq;
    private SpriteObj _incarnationReq;
    private SpriteObj _foodReq;
    private SpriteObj _xAntibodyReq;
    private SpriteObj _habitatReq;
    private SpriteObj _habitat;
    private SpriteObj _jogressMenu;
    private SpriteObj _dnaMenu;
    private SpriteObj _virusBusterReq;
    private SpriteObj _metalEmpireReq;
    private SpriteObj _dragonsRoarReq;
    private SpriteObj _jungleTrooperReq;
    private SpriteObj _deepSaverReq;
    private SpriteObj _nightmareSoldierReq;
    private SpriteObj _windGuardianReq;
    private SpriteObj _natureSpiritReq;
    private SpriteObj _darkAreaReq;
    private SpriteObj _noneReq;
    private SpriteObj _priority;
    private SpriteObj _priorityLabel;
    private SpriteObj[] _evolHistory;
    private SpriteObj _generationButton;
    private SpriteObj _generationAge;
    private boolean _generationMode;

    public int[] getTreePage() {
        return new int[]{this._preEvolutionsPage, this._evolutionsPage};
    }

    public void setTreePage(int[] pages) {
        this._preEvolutionsPage = pages[0];
        this._evolutionsPage = pages[1];
    }

    public void incTreePage() {
        if (this._currentInfo != null) {
            if (this._currentInfo.getVisibleEvolutions(null).size() > (this._evolutionsPage + 1) * 10) {
                ++this._evolutionsPage;
            }
            if (this._currentInfo.getVisiblePreEvolutions(null).size() > (this._preEvolutionsPage + 1) * 10) {
                ++this._preEvolutionsPage;
            }
            this.drawEvolutionMenu();
        }
    }

    public void decTreePage() {
        if (this._evolutionsPage - 1 >= 0) {
            --this._evolutionsPage;
        }
        if (this._preEvolutionsPage - 1 >= 0) {
            --this._preEvolutionsPage;
        }
        this.drawEvolutionMenu();
    }

    private boolean setJogressPage(int p) {
        byte max = (byte)(Math.ceil(this.getJogressCombinations(this._selectInfo.getNewAttribute()) / 4.0) - 1.0);
        byte old = this._jogressPage;
        this._jogressPage = p < 0 ? max : (p > max ? (byte)0 : (byte)p);
        if (old != this._jogressPage) {
            this.drawJogressAttributeCombinations(this._selectInfo.getNewAttribute());
        }
        return max > 0;
    }

    private double getJogressCombinations(Enum.Attribute a) {
        return this._digimon.getAffinity().getJogressCombinations(a).size();
    }

    private void setPage(int p) {
        boolean isJogress = this._selectInfo.getSpecialEvol() == Enum.SpecialEvolution.Jogress;
        byte previous = this._page;
        if (p > 2) {
            this._page = (byte)2;
        } else if (p < 0) {
            this._page = 0;
        } else {
            if (!isJogress && p == Page.Jogress.ordinal()) {
                p = 0;
            }
            this._page = (byte)p;
        }
        this._dna.setVisible(this._page == Page.DNA.ordinal() || this._page == Page.Jogress.ordinal());
        this.setupTabs(isJogress, previous);
        this._dnaMenu.setVisible(this._page == Page.DNA.ordinal());
        this._jogressMenu.setVisible(this._page == Page.Jogress.ordinal());
        this.drawDNAReqs();
    }

    private void setupTabs(boolean isJogress, int previous) {
        this._keyboard.getInteractiveButtons().remove(this._jogressLeftButton);
        this._keyboard.getInteractiveButtons().remove(this._jogressRightButton);
        this._keyboard.getInteractiveButtons().remove(this._collapsedRightButton);
        if (this._page == Page.DNA.ordinal()) {
            if (previous != Page.Jogress.ordinal()) {
                this._keyboard.insertBefore(this._bonusTab, this._reqTab);
            }
            this._keyboard.getInteractiveButtons().remove(this._bonusTab);
            if (isJogress && !this._keyboard.getInteractiveButtons().contains(this._jogressTab)) {
                this._keyboard.insertAfter(this._reqTab, this._jogressTab);
            } else if (!isJogress) {
                this._keyboard.getInteractiveButtons().remove(this._jogressTab);
            }
            if (this._collapsedRightButton.isVisible()) {
                if (isJogress) {
                    this._keyboard.insertAfter(this._jogressTab, this._collapsedRightButton);
                } else {
                    this._keyboard.insertAfter(this._reqTab, this._collapsedRightButton);
                }
            }
        } else if (this._page == Page.Jogress.ordinal()) {
            if (this._keyboard.getInteractiveButtons().contains(this._bonusTab)) {
                this._keyboard.insertBefore(this._bonusTab, this._reqTab);
            } else {
                this._keyboard.insertAfter(this._reqTab, this._bonusTab);
            }
            this._keyboard.getInteractiveButtons().remove(this._jogressTab);
            if (this._collapsedRightButton.isVisible()) {
                this._keyboard.insertAfter(this._bonusTab, this._collapsedRightButton);
                this._keyboard.insertAfter(this._collapsedRightButton, this._jogressLeftButton);
            } else {
                this._keyboard.insertAfter(this._bonusTab, this._jogressLeftButton);
            }
            this._keyboard.insertAfter(this._jogressLeftButton, this._jogressRightButton);
        } else {
            if (previous != Page.Jogress.ordinal()) {
                this._keyboard.insertBefore(this._reqTab, this._bonusTab);
            }
            this._keyboard.getInteractiveButtons().remove(this._reqTab);
            if (isJogress && !this._keyboard.getInteractiveButtons().contains(this._jogressTab)) {
                this._keyboard.insertAfter(this._bonusTab, this._jogressTab);
                this._keyboard.insertAfter(this._jogressTab, this._collapsedRightButton);
            } else if (!isJogress) {
                this._keyboard.getInteractiveButtons().remove(this._jogressTab);
                this._keyboard.insertAfter(this._bonusTab, this._collapsedRightButton);
            }
        }
        if (this._keyboard.getCursorPosition() > -1) {
            this._keyboard.moveCursor(this._keyboard.getCursorPosition() - 1);
        }
    }

    private boolean canIncDuplicatePage() {
        return this._duplicatePage + 1 < this._duplicates.size() || this._duplicates.size() > 2;
    }

    private boolean canDecDuplicatePage() {
        return this._duplicatePage - 1 >= 0 || this._duplicates.size() > 2;
    }

    private void incCollapsePage() {
        this._collapsePage = this._collapsePage + 1 >= this._collapsed.size() || this._collapsePage < 0 ? 0 : ++this._collapsePage;
    }

    public void incHistoryPage(int max) {
        if (this._historyPage + this._evolHistory.length < max) {
            ++this._historyPage;
        }
        this.populateHistory();
    }

    public void decHistoryPage() {
        this._historyPage = this._historyPage - 1 < 0 ? 0 : --this._historyPage;
        this.populateHistory();
    }

    public void incGenerationPage(int max) {
        if (this._generationPage + 8 < max) {
            ++this._generationPage;
        }
        this.populateGeneration();
    }

    public void decGenerationPage() {
        this._generationPage = this._generationPage - 1 < 0 ? 0 : --this._generationPage;
        this.populateGeneration();
    }

    public void incDuplicatePage() {
        if (this.canIncDuplicatePage()) {
            ++this._duplicatePage;
            if (this._duplicatePage > this._duplicates.size() - 1) {
                this._duplicatePage = 0;
            }
        }
        this.drawEvolutionMenu();
    }

    public void decDuplicatePage() {
        if (this.canDecDuplicatePage()) {
            --this._duplicatePage;
            if (this._duplicatePage < 0) {
                this._duplicatePage = this._duplicates.size() - 1;
            }
        }
        this.drawEvolutionMenu();
    }

    public EvolutionTree(PhysicalState digimon, ClockTic controller, byte scale, boolean isSound, String modFolder, String resourcesFolder, KeyboardCursor keyboard, SoundObj sounds, SpriteObj foodLabel, SpriteObj itemLabel, ArrayList<Habitat> habitats) {
        this.MOD_FOLDER = modFolder;
        this.RESOURCES_FOLDER = resourcesFolder;
        try {
            this.setTitle("DVPet - Evolution Tree");
            this._keyboard = keyboard;
            this._digimon = digimon;
            this._controller = controller;
            this._scale = scale;
            this._sounds = sounds;
            this._foodLabel = foodLabel;
            this._itemLabel = itemLabel;
            this._habitats = habitats;
            this._controller.getModel().getSettings().setSound(isSound);
            this.setUndecorated(true);
            ViewUtil.setBackgroundColor(this, ViewConfig._transparentMenus ? 0.0f : 1.0f);
            this.setDefaultCloseOperation(3);
            this.getContentPane().setLayout(null);
            ImageIcon icon = ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "PrgmIcon.png");
            this.setIconImage(icon.getImage());
            this.setLocationRelativeTo(null);
            this.setVisible(true);
            this._back = new DisplayPane(false);
            this._dna = new DisplayPane(false);
            this._dna.setVisible(true);
            this._global = new DisplayPane(false);
            this._display = new DisplayPane(false);
            this.scaleMenu();
            this.setSize(this._evolutionTree.getSizeX(), this._evolutionTree.getSizeY());
            int x = this._evolutionTree.getSizeX();
            int y = this._evolutionTree.getSizeY();
            int pad = 30;
            this._display.setSize(x, y - pad);
            this._back.setSize(x, y);
            this._display.setLocation(0, pad * this._scale);
            this._global.setSize(x, y - pad);
            this._global.setLocation(0, pad * this._scale);
            this.initTabs();
            this.initEvolutionMenu();
            this.add(this._searchBar);
            this.add(this._searchButton);
            this.add(this._reqTab);
            this.add(this._bonusTab);
            this.add(this._jogressTab);
            this.add(this._global);
            this.add(this._dna);
            this.add(this._display);
            this.add(this._back);
            this._display.add(this._border);
            this.drawEvolutionMenu();
            this._searchBar.setText(this.getCurrentSearchString());
            this._border.setVisible(false);
            this._keyboard.setCursorPosition(-1);
            this._back.requestFocus();
            ViewUtil.centerMain(this);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void scaleMenu() {
        ImageIcon i = ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolutionTree.png");
        Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
        while (i.getIconWidth() * this._scale > dim.width || i.getIconHeight() * this._scale > dim.height) {
            this._scale = (byte)(this._scale - 1);
            if (this._scale != 0) continue;
            this._scale = 1;
            break;
        }
        this._closeButton = new SpriteObj("", "", "", this._back, 13, 13, this._scale);
        this._closeButton.setLocX(147);
        this._closeButton.setLocY(1);
        this._closeButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "highlightClose.png");
        this._closeButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this._controller.onClose();
                if (EvolutionTree.this._closeButton != null) {
                    EvolutionTree.this._closeButton.removeIcon();
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                if (EvolutionTree.this._closeButton != null) {
                    EvolutionTree.this._closeButton.setAltIcon("highlightClose");
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (EvolutionTree.this._closeButton != null) {
                    EvolutionTree.this._closeButton.removeIcon();
                }
            }
        });
        this._evolutionTree = new SpriteObj(ViewUtil.resizeImage(i, (double)this._scale), this._back, 0, 0, this._scale);
        this._reducedScale = (double)this._scale * 0.66667;
    }

    private void initTabs() {
        this._reqTab = new SpriteObj("", "", "", null, 19, 10, this._scale);
        this._reqTab.setLoc(18, 329);
        this._reqTab.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolutionTreeTab.png");
        this._bonusTab = new SpriteObj("", "", "", null, 19, 10, this._scale);
        this._bonusTab.setLoc(40, 329);
        this._bonusTab.addAltSprite(this._reqTab.getAltSprite("evolutionTreeTab"), "evolutionTreeTab");
        this._jogressTab = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolutionTreeTabFull.png", null, 19, 10, this._scale);
        this._jogressTab.setLoc(62, 329);
        this._jogressTab.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolutionTreeTab.png");
        this._reqTab.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this.setPage(0);
                EvolutionTree.this._reqTab.removeIcon();
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (EvolutionTree.this._page != 0) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._select);
                    EvolutionTree.this._reqTab.setAltIcon("evolutionTreeTab");
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._reqTab.removeIcon();
            }
        });
        this._bonusTab.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this.setPage(1);
                EvolutionTree.this._bonusTab.removeIcon();
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (EvolutionTree.this._page != 1) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._select);
                    EvolutionTree.this._bonusTab.setAltIcon("evolutionTreeTab");
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._bonusTab.removeIcon();
            }
        });
        this._jogressTab.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this.setPage(2);
                EvolutionTree.this._jogressTab.setAltIcon("evolutionTreeTabFull");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (EvolutionTree.this._page != 2) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._select);
                    EvolutionTree.this._jogressTab.setAltIcon("evolutionTreeTab");
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._jogressTab.setAltIcon("evolutionTreeTabFull");
            }
        });
    }

    private void setBorder(SpriteObj o, int xPad, int yPad, int girth, boolean visible) {
        this._border.setBorder(BorderFactory.createLineBorder(Color.BLACK, girth * this._scale));
        this._border.setBounds(o.getLocX() - xPad * this._scale, o.getLocY() - yPad * this._scale, o.getSizeX() + xPad * 2 * this._scale, o.getSizeY() + yPad * 2 * this._scale);
        this._border.setVisible(visible);
    }

    private void initEvolutionMenu() {
        int currentIndex;
        int i;
        this._locked = ViewUtil.resizeImage(ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "locked.png"), (double)this._scale);
        this._null = ViewUtil.resizeImage(ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "null.png"), (double)this._scale);
        Font ttfBase = null;
        Font bit = null;
        try (InputStream stream = Utility.getInputStream(this.MOD_FOLDER, this.RESOURCES_FOLDER, "font.ttf");){
            ttfBase = Font.createFont(0, stream);
            bit = ttfBase.deriveFont(0, 31 * this._scale);
        }
        catch (Exception ex) {
            CrashEntry.generateEntry(ex);
            ex.printStackTrace();
        }
        MouseAdapter ma = new MouseAdapter(){
            boolean pressed = false;

            @Override
            public void mousePressed(MouseEvent event) {
                this.pressed = true;
                EvolutionTree.this._posx = event.getX();
                EvolutionTree.this._posy = event.getY();
            }

            @Override
            public void mouseReleased(MouseEvent event) {
                this.pressed = false;
            }

            @Override
            public void mouseDragged(MouseEvent event) {
                if (this.pressed) {
                    EvolutionTree.this.setLocation(event.getXOnScreen() - EvolutionTree.this._posx, event.getYOnScreen() - EvolutionTree.this._posy);
                }
            }
        };
        this.addMouseListener(ma);
        this.addMouseMotionListener(ma);
        final PhysicalState digimon = this._controller.getModel().getDigimon();
        Evolution evol = digimon.getEvolution();
        this._generationButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "generationHistory.png", this._display, 27, 27, this._scale);
        this._generationButton.setLoc(449, 20);
        this._generationButton.addAltSprite(ViewUtil.getTransparentImage(this._generationButton.getAltSprite("generationHistory"), 0.5f), "tGenerationHistory");
        this._generationButton.setAltIcon("tGenerationHistory");
        this._generationButton.addMouseListener(new MouseAdapter(this){
            final /* synthetic */ EvolutionTree this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void mousePressed(MouseEvent e) {
                this.this$0._sounds.playSound(SoundConfig._click);
                this.this$0._generationMode = !this.this$0._generationMode;
                int page = digimon.getEvolHistory().size() - this.this$0._evolHistory.length;
                this.this$0._historyPage = page < 0 ? 0 : page;
                if (this.this$0._generationMode) {
                    int p = this.this$0._digimon.getGenerationHistory().size() - 1;
                    this.this$0._evolutionsPage = 0;
                    this.this$0.setGenerationLoc();
                    this.this$0.selectDigimon(p);
                } else {
                    this.this$0._preEvolutionsPage = 0;
                    this.this$0.selectDigimon(this.this$0._digimon.getIndex());
                    this.this$0.selectDigimon(this.this$0._digimon.getIndex());
                    this.this$0.setDefaultLoc();
                }
                this.this$0.drawEvolutionMenu();
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                this.this$0._sounds.playSound(SoundConfig._select);
                this.this$0._generationButton.setAltIcon("generationHistory");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                this.this$0._generationButton.setAltIcon("tGenerationHistory");
            }
        });
        this._searchButton = new SpriteObj("", "", "", null, 16, 15, this._scale);
        this._searchButton.setLoc(481, 23);
        this._searchButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "search.png");
        this._searchButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (EvolutionTree.this.selectSearchDigimon(EvolutionTree.this._searchBar.getText().trim())) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._searchButton.setAltIcon("search");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._searchButton.removeIcon();
            }
        });
        this._rightButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "arrow.png", this._display, 12, 24, this._scale);
        this._rightButton.setLoc(251, 150);
        this._rightButton.setVisible(false);
        this._rightButton.getAltSprite("arrow").setDescription("right");
        this._rightButton.addAltSprite(ViewUtil.getTransparentImage(this._rightButton.getAltSprite("right"), 0.25f), "tRight");
        this._rightButton.setAltIcon("tRight");
        this._rightButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                if (!EvolutionTree.this._generationMode) {
                    EvolutionTree.this._controller.onCycleRight();
                    EvolutionInfo ev = (EvolutionInfo)EvolutionTree.this._duplicates.get(EvolutionTree.this._duplicatePage);
                    EvolutionTree.this.selectDigimon(ev.getIndex());
                    EvolutionTree.this.selectDigimon(ev.getIndex());
                } else {
                    EvolutionTree.this.incGenerationPage(EvolutionTree.this._digimon.getGenerationHistory().get(EvolutionTree.this._preEvolutionsPage).size());
                }
                EvolutionTree.this._keyboard.setCursorPosition(-1);
                EvolutionTree.this._rightButton.setAltIcon("tRight");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._rightButton.setAltIcon("right");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._rightButton.setAltIcon("tRight");
            }
        });
        this._leftButton = new SpriteObj("", "", "", this._display, 12, 24, this._scale);
        this._leftButton.setLoc(199, 150);
        this._leftButton.setVisible(false);
        this._leftButton.addAltSprite(ViewUtil.flipHorizontally(this._rightButton.getAltSprite("right")), "left");
        this._leftButton.addAltSprite(ViewUtil.getTransparentImage(this._leftButton.getAltSprite("left"), 0.25f), "tLeft");
        this._leftButton.setAltIcon("tLeft");
        this._leftButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                if (!EvolutionTree.this._generationMode) {
                    EvolutionTree.this._controller.onCycleLeft();
                    EvolutionTree.this.selectDigimon(((EvolutionInfo)EvolutionTree.this._duplicates.get(EvolutionTree.this._duplicatePage)).getIndex());
                    EvolutionTree.this.selectDigimon(((EvolutionInfo)EvolutionTree.this._duplicates.get(EvolutionTree.this._duplicatePage)).getIndex());
                } else {
                    EvolutionTree.this.decGenerationPage();
                }
                EvolutionTree.this._keyboard.setCursorPosition(-1);
                EvolutionTree.this._leftButton.setAltIcon("tLeft");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._leftButton.setAltIcon("left");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._leftButton.setAltIcon("tLeft");
            }
        });
        this._upButton = new SpriteObj("", "", "", this._display, 24, 12, this._scale);
        this._upButton.setLoc(219, 131);
        this._upButton.setVisible(false);
        Icon up = ViewUtil.getRotatedIcon(3, this._rightButton.getAltSprite("right"));
        this._upButton.addAltSprite(up, "up");
        this._upButton.addAltSprite(ViewUtil.getTransparentImage(this._upButton.getAltSprite("up"), 0.25f), "tUp");
        this._upButton.setAltIcon("tUp");
        this._upButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this._controller.onCycleUp();
                EvolutionTree.this._keyboard.setCursorPosition(-1);
                EvolutionTree.this._upButton.setAltIcon("tUp");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._upButton.setAltIcon("up");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._upButton.setAltIcon("tUp");
            }
        });
        this._historyUpButton = new SpriteObj("", "", "", this._display, 24, 12, this._scale);
        this._historyUpButton.addAltSprite(this._upButton.getAltSprite("up"), "up");
        this._historyUpButton.addAltSprite(this._upButton.getAltSprite("tUp"), "tUp");
        this._historyUpButton.setAltIcon("tUp");
        this._historyUpButton.setVisible(false);
        this._historyUpButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this.decHistoryPage();
                EvolutionTree.this._keyboard.setCursorPosition(-1);
                EvolutionTree.this._historyUpButton.setAltIcon("tUp");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._historyUpButton.setAltIcon("up");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._historyUpButton.setAltIcon("tUp");
            }
        });
        this._downButton = new SpriteObj("", "", "", this._display, 24, 12, this._scale);
        this._downButton.setLoc(219, 181);
        this._downButton.setVisible(false);
        Icon down = ViewUtil.getRotatedIcon(1, this._rightButton.getAltSprite("right"));
        this._downButton.addAltSprite(down, "down");
        this._downButton.addAltSprite(ViewUtil.getTransparentImage(this._downButton.getAltSprite("down"), 0.25f), "tDown");
        this._downButton.setAltIcon("tDown");
        this._downButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                EvolutionTree.this._keyboard.setCursorPosition(-1);
                EvolutionTree.this._downButton.setAltIcon("tDown");
                EvolutionTree.this._controller.onCycleDown();
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._downButton.setAltIcon("down");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._downButton.setAltIcon("tDown");
            }
        });
        this._historyDownButton = new SpriteObj("", "", "", this._display, 24, 12, this._scale);
        this._historyDownButton.setVisible(false);
        this._historyDownButton.addAltSprite(this._downButton.getAltSprite("down"), "down");
        this._historyDownButton.addAltSprite(this._downButton.getAltSprite("tDown"), "tDown");
        this._historyDownButton.setAltIcon("tDown");
        this._historyDownButton.addMouseListener(new MouseAdapter(this){
            final /* synthetic */ EvolutionTree this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void mousePressed(MouseEvent e) {
                this.this$0._sounds.playSound(SoundConfig._click);
                this.this$0._keyboard.setCursorPosition(-1);
                this.this$0._historyDownButton.setAltIcon("tDown");
                this.this$0.incHistoryPage(digimon.getEvolHistory().size());
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                this.this$0._sounds.playSound(SoundConfig._select);
                this.this$0._historyDownButton.setAltIcon("down");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                this.this$0._historyDownButton.setAltIcon("tDown");
            }
        });
        int scale = (int)(3.0 / (double)this._scale * (double)this._scale);
        this._jogressLeftButton = new SpriteObj("", "", "", this._dna, 36, 72, this._scale);
        this._jogressLeftButton.addAltSprite(ViewUtil.resizeImage(this._leftButton.getAltSprite("left"), (double)scale), "jogressLeftButton");
        this._jogressLeftButton.addAltSprite(ViewUtil.resizeImage(this._leftButton.getAltSprite("tLeft"), (double)scale), "tJogressLeftButton");
        this._jogressLeftButton.setAltIcon("tJogressLeftButton");
        this._jogressLeftButton.setLoc(17, 81);
        this._jogressLeftButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (EvolutionTree.this.setJogressPage(EvolutionTree.this._jogressPage - 1)) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._click);
                } else {
                    EvolutionTree.this._sounds.playSound(SoundConfig._error);
                }
                EvolutionTree.this._jogressLeftButton.setAltIcon("tJogressLeftButton");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._jogressLeftButton.setAltIcon("jogressLeftButton");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._jogressLeftButton.setAltIcon("tJogressLeftButton");
            }
        });
        this._jogressRightButton = new SpriteObj("", "", "", this._dna, 36, 72, this._scale);
        this._jogressRightButton.addAltSprite(ViewUtil.resizeImage(this._rightButton.getAltSprite("right"), (double)scale), "jogressRightButton");
        this._jogressRightButton.addAltSprite(ViewUtil.resizeImage(this._rightButton.getAltSprite("tRight"), (double)scale), "tJogressRightButton");
        this._jogressRightButton.setAltIcon("tJogressRightButton");
        this._jogressRightButton.setLoc(459, 81);
        this._jogressRightButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (EvolutionTree.this.setJogressPage(EvolutionTree.this._jogressPage + 1)) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._click);
                } else {
                    EvolutionTree.this._sounds.playSound(SoundConfig._error);
                }
                EvolutionTree.this._jogressRightButton.setAltIcon("tJogressRightButton");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._jogressRightButton.setAltIcon("jogressRightButton");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._jogressRightButton.setAltIcon("tJogressRightButton");
            }
        });
        this._collapsedRightButton = new SpriteObj("", "", "", this._global, 12, 24, this._scale);
        this._collapsedRightButton.addAltSprite(this._rightButton.getAltSprite("right"), "right");
        this._collapsedRightButton.addAltSprite(ViewUtil.getTransparentImage(this._rightButton.getAltSprite("right"), 0.25f), "tRight");
        this._collapsedRightButton.setAltIcon("tRight");
        this._collapsedRightButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                EvolutionTree.this._sounds.playSound(SoundConfig._click);
                if (!EvolutionTree.this._generationMode && !EvolutionTree.this._collapsed.isEmpty()) {
                    EvolutionTree.this.incCollapsePage();
                    EvolutionInfo ev = (EvolutionInfo)EvolutionTree.this._collapsed.get(EvolutionTree.this._collapsePage);
                    EvolutionTree.this._lastDigimon = ev;
                    EvolutionTree.this.selectDigimon(ev.getIndex());
                    if (EvolutionTree.this._lastEvolButtonPressed != null) {
                        EvolutionTree.this._lastEvolButtonPressed.setIcon(EvolutionTree.this._selectDigimon.getIcon());
                    }
                }
                EvolutionTree.this._keyboard.setCursorPosition(-1);
                EvolutionTree.this._collapsedRightButton.setAltIcon("tRight");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                EvolutionTree.this._sounds.playSound(SoundConfig._select);
                EvolutionTree.this._collapsedRightButton.setAltIcon("right");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                EvolutionTree.this._collapsedRightButton.setAltIcon("tRight");
            }
        });
        this._evolHistory = new SpriteObj[5];
        this._evolEvolutions = new SpriteObj[10];
        this._evolPreEvolutions = new SpriteObj[10];
        for (i = 0; i < this._evolHistory.length; ++i) {
            currentIndex = i;
            this._evolHistory[i] = new SpriteObj("", "", "", this._display, 32, 32, this._scale);
            this._evolHistory[i].setVisible(false);
            this._evolHistory[i].setHorizontalAlignment(0);
            final SpriteObj obj = this._evolHistory[i];
            this._evolHistory[i].addMouseListener(new MouseAdapter(this){
                final /* synthetic */ EvolutionTree this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void mousePressed(MouseEvent e) {
                    if (!this.this$0._generationMode && obj.getIcon() != null) {
                        this.this$0.selectDigimon(this.this$0.getDigimon(digimon.getEvolHistory().get(currentIndex + this.this$0._historyPage)[0]), false);
                        this.this$0.processDuplicates();
                        this.this$0._sounds.playSound(SoundConfig._click);
                    }
                }

                @Override
                public void mouseEntered(MouseEvent e) {
                    if (!this.this$0._generationMode && obj.getIcon() != null) {
                        this.this$0.setBorder(this.this$0._evolHistory[currentIndex], 4, 4, 2, true);
                        this.this$0._sounds.playSound(SoundConfig._select);
                    }
                }

                @Override
                public void mouseExited(MouseEvent e) {
                    if (!this.this$0._generationMode && obj.getIcon() != null) {
                        this.this$0._border.setVisible(false);
                    }
                }
            });
        }
        for (i = 0; i < 10; ++i) {
            currentIndex = i;
            this._evolEvolutions[i] = new SpriteObj("", "", "", this._display, 32, 32, this._scale);
            this._evolEvolutions[i].setVisible(false);
            this._evolEvolutions[i].setHorizontalAlignment(0);
            this._evolEvolutions[i].addMouseListener(new MouseAdapter(this){
                final /* synthetic */ EvolutionTree this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void mousePressed(MouseEvent e) {
                    if (!this.this$0._generationMode) {
                        this.this$0.restoreOriginalCollapsedIcon();
                        this.this$0._lastEvolButtonPressed = this.this$0._evolEvolutions[currentIndex];
                        this.this$0.selectDigimon(currentIndex + this.this$0._evolEvolutions.length * this.this$0._evolutionsPage, true);
                        if (!Config._evolHint && !this.this$0._selectInfo.getUnlocked()) {
                            this.this$0._sounds.playSound(SoundConfig._error);
                        } else {
                            this.this$0._sounds.playSound(SoundConfig._click);
                        }
                    } else if (currentIndex == 0 || currentIndex == 8) {
                        this.this$0._generationPage = 0;
                        this.this$0.selectDigimon(this.this$0._preEvolutionsPage + (currentIndex == 0 ? -1 : (currentIndex == 8 ? 1 : 0)), false);
                        this.this$0._border.setVisible(false);
                        this.this$0._sounds.playSound(SoundConfig._click);
                    }
                }

                @Override
                public void mouseEntered(MouseEvent e) {
                    this.this$0._sounds.playSound(SoundConfig._select);
                    this.this$0.setBorder(this.this$0._evolEvolutions[currentIndex], 4, 4, 2, true);
                }

                @Override
                public void mouseExited(MouseEvent e) {
                    this.this$0._border.setVisible(false);
                }
            });
            this._evolPreEvolutions[i] = new SpriteObj("", "", "", this._display, 32, 32, this._scale);
            this._evolPreEvolutions[i].setVisible(false);
            this._evolPreEvolutions[i].setHorizontalAlignment(0);
            this._evolPreEvolutions[i].addMouseListener(new MouseAdapter(this){
                final /* synthetic */ EvolutionTree this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void mousePressed(MouseEvent e) {
                    if (!this.this$0._generationMode) {
                        this.this$0.restoreOriginalCollapsedIcon();
                        this.this$0._lastEvolButtonPressed = this.this$0._evolPreEvolutions[currentIndex];
                        this.this$0.selectDigimon(currentIndex + this.this$0._evolPreEvolutions.length * this.this$0._preEvolutionsPage, false);
                        if (!Config._evolHint && !this.this$0._selectInfo.getUnlocked()) {
                            this.this$0._sounds.playSound(SoundConfig._error);
                        } else {
                            this.this$0._sounds.playSound(SoundConfig._click);
                        }
                    } else if (currentIndex == 0 || currentIndex == 8) {
                        this.this$0._generationPage = 0;
                        this.this$0.selectDigimon(this.this$0._preEvolutionsPage + (currentIndex == 0 ? -1 : (currentIndex == 8 ? 1 : 0)), false);
                        this.this$0._border.setVisible(false);
                        this.this$0._sounds.playSound(SoundConfig._click);
                    }
                }

                @Override
                public void mouseEntered(MouseEvent e) {
                    if (this.this$0._generationMode && (currentIndex == 0 || currentIndex == 8) || !this.this$0._generationMode) {
                        this.this$0._sounds.playSound(SoundConfig._select);
                        this.this$0.setBorder(this.this$0._evolPreEvolutions[currentIndex], 4, 4, 2, true);
                    }
                }

                @Override
                public void mouseExited(MouseEvent e) {
                    if (this.this$0._generationMode && (currentIndex == 0 || currentIndex == 8) || !this.this$0._generationMode) {
                        this.this$0._border.setVisible(false);
                    }
                }
            });
        }
        this.setDefaultLoc();
        this._currentDigimon = new SpriteObj("", "", "", this._display, 32, 32, this._scale);
        this._currentDigimon.setHorizontalAlignment(0);
        this._currentDigimon.setLoc(215, 146);
        this._currentDigimon.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!EvolutionTree.this._generationMode) {
                    EvolutionTree.this._selectInfo = EvolutionTree.this._currentInfo;
                    EvolutionTree.this._collapsed.clear();
                    EvolutionTree.this.setPage(0);
                    EvolutionTree.this.populateReqs();
                    EvolutionTree.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!EvolutionTree.this._generationMode) {
                    EvolutionTree.this._sounds.playSound(SoundConfig._select);
                    EvolutionTree.this.setBorder(EvolutionTree.this._currentDigimon, 4, 4, 2, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                EvolutionTree.this._border.setVisible(false);
            }
        });
        this._attributeLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "red.png", this._global, 14, 14, this._scale);
        this._attributeLabel.setLoc(54, 337);
        this._attributeLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "green.png");
        this._attributeLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "yellow.png");
        this._fieldLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fields.png", this._global, 14, 14, 4, this._scale);
        this._fieldLabel.setLocX(this._attributeLabel.getLocX() / this._scale + this._attributeLabel.getSizeX() / this._scale + 3);
        this._fieldLabel.setLocY(this._attributeLabel.getLocY() / this._scale);
        this._elementLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "elements.png", this._global, 22, 15, 1, this._scale);
        this._elementLabel.setVerticalAlignment(1);
        this._priority = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "favoriteMenu.png", this._global, this._scale);
        this._priorityLabel = new SpriteObj("", "", "", this._global, 30, 13, this._scale);
        this._priorityLabel.setFont(ttfBase.deriveFont(1, 21 * this._scale));
        this._priorityLabel.setForeground(Color.BLACK);
        this._specialEvol = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "specialEvol.png", this._global, 16, 16, 1, this._scale);
        this._specialEvol.setLoc(220, 312);
        this._specialEvol.setVisible(false);
        this._selectDigimon = new SpriteObj("", "", "", this._global, 32, 32, this._scale);
        this._selectDigimon.setLoc(19, 317);
        this._generationAge = new SpriteObj("", "", "", this._display, 60, 25, this._scale);
        this._generationAge.setLoc(this._currentDigimon.getLocX() / this._scale + this._currentDigimon.getSizeX() / this._scale / 3, this._currentDigimon.getLocY() / this._scale - this._generationAge.getSizeY() / this._scale);
        this._generationAge.setBorder(null);
        this._generationAge.setFont(bit);
        this._generationAge.setForeground(Color.BLACK);
        this._name = new SpriteObj("", "", "", this._global, 185, 33, this._scale);
        this._name.setLoc(53, 308);
        this._name.setBorder(null);
        this._name.setFont(bit);
        this._name.setForeground(Color.BLACK);
        this._vaccineReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._vaccineReq.setLoc(62, 361);
        this._vaccineReq.setBorder(null);
        this._vaccineReq.setFont(bit);
        this._vaccineReq.setForeground(Color.BLACK);
        this._dataReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._dataReq.setLoc(this._vaccineReq.getLocX() / this._scale, 404);
        this._dataReq.setBorder(null);
        this._dataReq.setFont(bit);
        this._dataReq.setForeground(Color.BLACK);
        this._virusReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._virusReq.setLoc(this._dataReq.getLocX() / this._scale, 448);
        this._virusReq.setBorder(null);
        this._virusReq.setFont(bit);
        this._virusReq.setForeground(Color.BLACK);
        this._weightReq = new SpriteObj("", "", "", this._display, 65, 36, this._scale);
        this._weightReq.setLoc(347, 359);
        this._weightReq.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weightNormal.png", 2.0 * (double)this._scale), "weightNormal");
        this._weightReq.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weightOver.png", 2.0 * (double)this._scale), "weightOver");
        this._weightReq.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weightUnder.png", 2.0 * (double)this._scale), "weightUnder");
        this._weightReq.setBorder(null);
        this._weightReq.setFont(bit);
        this._weightReq.setForeground(Color.BLACK);
        this._mistakeReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._mistakeReq.setLoc(326, 317);
        this._mistakeReq.setBorder(null);
        this._mistakeReq.setFont(bit);
        this._mistakeReq.setForeground(Color.BLACK);
        this._overeatReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._overeatReq.setLoc(289, this._vaccineReq.getLocY() / this._scale);
        this._overeatReq.setBorder(null);
        this._overeatReq.setFont(bit);
        this._overeatReq.setForeground(Color.BLACK);
        this._disturbReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._disturbReq.setLoc(this._overeatReq.getLocX() / this._scale, this._dataReq.getLocY() / this._scale);
        this._disturbReq.setBorder(null);
        this._disturbReq.setFont(bit);
        this._disturbReq.setForeground(Color.BLACK);
        this._tempReq = new SpriteObj("", "", "", this._display, 100, 36, this._scale);
        this._tempReq.setLoc(367, this._disturbReq.getLocY() / this._scale);
        this._tempReq.setBorder(null);
        this._tempReq.setFont(bit);
        this._tempReq.setForeground(Color.BLACK);
        this._sickReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._sickReq.setLoc(408, this._mistakeReq.getLocY() / this._scale);
        this._sickReq.setBorder(null);
        this._sickReq.setFont(bit);
        this._sickReq.setForeground(Color.BLACK);
        this._injReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._injReq.setLoc(477, this._mistakeReq.getLocY() / this._scale);
        this._injReq.setBorder(null);
        this._injReq.setFont(bit);
        this._injReq.setForeground(Color.BLACK);
        this._battleReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._battleReq.setLoc(177, 351);
        this._battleReq.setBorder(null);
        this._battleReq.setFont(bit);
        this._battleReq.setForeground(Color.BLACK);
        this._winReq = new SpriteObj("", "", "", this._display, 65, 36, this._scale);
        this._winReq.setLoc(16 + this._battleReq.getLocX() / this._scale, 19 + this._battleReq.getLocY() / this._scale);
        this._winReq.setBorder(null);
        this._winReq.setFont(bit);
        this._winReq.setForeground(Color.BLACK);
        this._obedienceReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._obedienceReq.setLoc(478, this._disturbReq.getLocY() / this._scale);
        this._obedienceReq.setBorder(null);
        this._obedienceReq.setFont(bit);
        this._obedienceReq.setForeground(Color.BLACK);
        this._timeReq = new SpriteObj("", "", "", this._display, 30, 30, this._scale);
        this._timeReq.setLoc(this._disturbReq.getLocX() / this._scale + 2, 450);
        this._timeReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "morning.png");
        this._timeReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "noon.png");
        this._timeReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "night.png");
        this._timeReq.setBorder(null);
        this._timeReq.setFont(bit);
        this._timeReq.setForeground(Color.BLACK);
        this._moodReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._moodReq.setLoc(this._obedienceReq.getLocX() / this._scale, this._vaccineReq.getLocY() / this._scale - 2);
        this._moodReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "happy.png");
        this._moodReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "unhappy.png");
        this._moodReq.setBorder(null);
        this._moodReq.setFont(bit);
        this._moodReq.setForeground(Color.BLACK);
        this._levelReq = new SpriteObj("", "", "", this._display, 86, 36, this._scale);
        this._levelReq.setLoc(170, 406);
        this._levelReq.setBorder(null);
        this._levelReq.setFont(bit);
        this._levelReq.setForeground(Color.BLACK);
        this._habitatReq = new SpriteObj("", "", "", this._display, 110, 36, this._scale);
        this._habitatReq.setLoc(401, 447);
        this._habitatReq.setBorder(null);
        this._habitatReq.setFont(bit);
        this._habitatReq.setForeground(Color.BLACK);
        this._habitat = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._display, 26, 26, this._scale);
        this._habitat.setLoc(371, 450);
        this._incarnationReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._incarnationReq.setLoc(5 + this._levelReq.getLocX() / this._scale, this._virusReq.getLocY() / this._scale);
        this._incarnationReq.setBorder(null);
        this._incarnationReq.setFont(bit);
        this._incarnationReq.setForeground(Color.BLACK);
        this._foodReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._foodReq.setLoc(394, 359);
        this._foodReq.setBorder(null);
        this._foodReq.setFont(bit);
        this._foodReq.setForeground(Color.BLACK);
        this._xAntibodyReq = new SpriteObj("", "", "", this._display, 55, 36, this._scale);
        this._xAntibodyReq.setLoc(254, 314);
        this._xAntibodyReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "xAntibodyReq.png");
        this._xAntibodyReq.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "xAntibodyNoReq.png");
        this._xAntibodyReq.setBorder(null);
        this._xAntibodyReq.setFont(bit);
        this._xAntibodyReq.setForeground(Color.BLACK);
        this._virusBusterReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._virusBusterReq.setLoc(391, 14);
        this._virusBusterReq.setBorder(null);
        this._virusBusterReq.setFont(bit);
        this._virusBusterReq.setForeground(Color.BLACK);
        this._metalEmpireReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._metalEmpireReq.setLoc(60, 59);
        this._metalEmpireReq.setBorder(null);
        this._metalEmpireReq.setFont(bit);
        this._metalEmpireReq.setForeground(Color.BLACK);
        this._dragonsRoarReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._dragonsRoarReq.setLoc(222, this._metalEmpireReq.getLocY() / this._scale);
        this._dragonsRoarReq.setBorder(null);
        this._dragonsRoarReq.setFont(bit);
        this._dragonsRoarReq.setForeground(Color.BLACK);
        this._jungleTrooperReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._jungleTrooperReq.setLoc(this._virusBusterReq.getLocX() / this._scale, this._metalEmpireReq.getLocY() / this._scale);
        this._jungleTrooperReq.setBorder(null);
        this._jungleTrooperReq.setFont(bit);
        this._jungleTrooperReq.setForeground(Color.BLACK);
        this._deepSaverReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._deepSaverReq.setLoc(this._metalEmpireReq.getLocX() / this._scale, 103);
        this._deepSaverReq.setBorder(null);
        this._deepSaverReq.setFont(bit);
        this._deepSaverReq.setForeground(Color.BLACK);
        this._nightmareSoldierReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._nightmareSoldierReq.setLoc(this._dragonsRoarReq.getLocX() / this._scale, this._deepSaverReq.getLocY() / this._scale);
        this._nightmareSoldierReq.setBorder(null);
        this._nightmareSoldierReq.setFont(bit);
        this._nightmareSoldierReq.setForeground(Color.BLACK);
        this._windGuardianReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._windGuardianReq.setLoc(this._virusBusterReq.getLocX() / this._scale, this._deepSaverReq.getLocY() / this._scale);
        this._windGuardianReq.setBorder(null);
        this._windGuardianReq.setFont(bit);
        this._windGuardianReq.setForeground(Color.BLACK);
        this._natureSpiritReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._natureSpiritReq.setLoc(this._metalEmpireReq.getLocX() / this._scale, 145);
        this._natureSpiritReq.setBorder(null);
        this._natureSpiritReq.setFont(bit);
        this._natureSpiritReq.setForeground(Color.BLACK);
        this._darkAreaReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._darkAreaReq.setLoc(this._dragonsRoarReq.getLocX() / this._scale, this._natureSpiritReq.getLocY() / this._scale);
        this._darkAreaReq.setBorder(null);
        this._darkAreaReq.setFont(bit);
        this._darkAreaReq.setForeground(Color.BLACK);
        this._noneReq = new SpriteObj("", "", "", this._dna, 55, 36, this._scale);
        this._noneReq.setLoc(this._virusBusterReq.getLocX() / this._scale, this._natureSpiritReq.getLocY() / this._scale);
        this._noneReq.setBorder(null);
        this._noneReq.setFont(bit);
        this._noneReq.setForeground(Color.BLACK);
        this._searchBar = new JTextField();
        this._searchBar.setDocument(new JTextFieldLimit(42));
        this._searchBar.setEditable(true);
        this._searchBar.setText("https://www.dvpet.net/herculeskabuterimon");
        this._searchBar.setFont(bit);
        this._searchBar.setForeground(Color.BLACK);
        this._searchBar.setBounds(96 * this._scale, 21 * this._scale, 380 * this._scale, 22 * this._scale);
        this._searchBar.setBackground(new Color(0, 0, 0, 0));
        this._searchBar.setOpaque(false);
        this._searchBar.setBorder(BorderFactory.createEmptyBorder());
        this._searchBar.addActionListener(new ActionListener(){

            @Override
            public void actionPerformed(ActionEvent evt) {
                if (!EvolutionTree.this._generationMode) {
                    boolean success = EvolutionTree.this.selectSearchDigimon(EvolutionTree.this._searchBar.getText().trim());
                    if (!success || !ViewConfig._enableTextFieldKeyboardCursor) {
                        // empty if block
                    }
                    EvolutionTree.this._border.setVisible(false);
                    EvolutionTree.this._keyboard.setCursorPosition(-1);
                    EvolutionTree.this._back.requestFocus();
                }
            }
        });
        this._searchBar.addMouseListener(new MouseAdapter(){

            @Override
            public void mouseClicked(MouseEvent e) {
                if (ViewConfig._enableTextFieldKeyboardCursor) {
                    EvolutionTree.this._searchBar.setText("");
                } else {
                    EvolutionTree.this._searchBar.select(0, EvolutionTree.this._searchBar.getText().length());
                }
                EvolutionTree.this._keyboard.setCursorPosition(EvolutionTree.this._keyboard.getTextFieldPosition());
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!ViewConfig._enableTextFieldKeyboardCursor) {
                    EvolutionTree.this._searchBar.select(EvolutionTree.this._searchBar.getText().length(), EvolutionTree.this._searchBar.getText().length());
                }
                EvolutionTree.this._back.requestFocus();
                EvolutionTree.this._border.setVisible(false);
                EvolutionTree.this._keyboard.setCursorPosition(-1);
            }

            @Override
            public void mouseEntered(MouseEvent e) {
            }
        });
        this._searchBar.addKeyListener(new KeyAdapter(){

            @Override
            public void keyTyped(KeyEvent e) {
                if (ViewConfig._enableTextFieldKeyboardCursor) {
                    e.consume();
                }
            }
        });
        int page = digimon.getEvolHistory().size() - this._evolHistory.length;
        this._historyPage = page < 0 ? 0 : page;
        this._jogressMenu = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolutionTreeAttributeCombos.png", this._dna, 513, 188, this._scale);
        this._jogressMenu.setLoc(0, 0);
        this._jogressMenu.setVisible(false);
        this._dnaMenu = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolutionTreeBonusPage.png", this._dna, 513, 188, this._scale);
        this._dnaMenu.setLoc(0, 0);
        this._dnaMenu.setVisible(false);
        this._dna.setSize(this._dnaMenu.getSizeX(), this._dnaMenu.getSizeY());
        this._dna.setLocation(8 * this._scale, 333 * this._scale);
        this._selectInfo = this._currentInfo = this._digimon.getEvolution().getDigimon(this._digimon.getIndex());
        this.processDuplicates();
    }

    public void setupTree() {
        this.populateTree();
        this.populateReqs();
    }

    public void populateTree() {
        Icon icon = this._locked;
        if (this._currentInfo.getUnlocked()) {
            icon = this.getEvolutionInfoIcon(this._currentInfo);
        }
        this._currentDigimon.setIcon(icon);
        this.populateHistory();
        try {
            if (!this._generationMode) {
                this.populateEvolutions(this._currentInfo.getVisiblePreEvolutions(this._lastDigimon), this._evolPreEvolutions, this._preEvolutionsPage);
                this.populateEvolutions(this._currentInfo.getVisibleEvolutions(this._lastDigimon), this._evolEvolutions, this._evolutionsPage);
            } else {
                this.populateGeneration();
            }
        }
        catch (IndexOutOfBoundsException e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private boolean changeColor(boolean check, String text) {
        return check && !text.equals("--");
    }

    private void populateReqs() {
        Icon i;
        double priority;
        Evolution evol = this._digimon.getEvolution();
        boolean check = Config._changeFulfilledReqColor && this._currentInfo.getIndex() == this._digimon.getIndex() && this._currentInfo.getEvolutions().contains(this._selectInfo);
        String y = ViewConfig._fulfilledReqColor;
        char[] c = new char[]{'<', '>', '='};
        boolean dna = check ? (evol.hasDNARequirement(this._selectInfo, this._digimon) ? evol.testDNA(this._selectInfo, this._digimon) : false) : false;
        boolean canEvol = check ? evol.checkEvolReq(this._digimon, this._selectInfo, true, 101) : false;
        double d = priority = check && canEvol ? evol.getFulfilledReq(this._selectInfo, this._digimon) : 0.0;
        if (canEvol && dna && !evol.getDNA()) {
            y = ViewConfig._allDNAFulfilledColor;
        }
        if (this._selectInfo.getUnlocked()) {
            Icon icon = this.getEvolutionInfoIcon(this._selectInfo);
            this._selectDigimon.setIcon(icon);
            this._name.setText(this._selectInfo.getName());
        } else {
            this._selectDigimon.setIcon(this._locked);
            this._name.setText("--");
        }
        this.checkElement();
        this._name.setLocX(this._selectDigimon.getLocX() / this._scale + this._selectDigimon.getSizeX() / this._scale + 2);
        this.checkSpecialEvol();
        this._jogressTab.setVisible(this._selectInfo.getSpecialEvol() == Enum.SpecialEvolution.Jogress);
        this.checkCollapsed();
        int total = this._digimon.getVaccinePower() + this._digimon.getDataPower() + this._digimon.getVirusPower();
        this._vaccineReq.setText(this.attributeInfoToString(this._selectInfo.getVaccinePower()[0]) + (this._selectInfo.getVaccinePower()[1].getKey() != Enum.Condition.None ? " | " + this.attributeInfoToString(this._selectInfo.getVaccinePower()[1]) : ""));
        if (this.changeColor(check, this._vaccineReq.getText()) && evol.testAttribute(this._selectInfo.getVaccinePower()[0], this._digimon.getVaccinePower(), total) && evol.testAttribute(this._selectInfo.getVaccinePower()[1], this._digimon.getVaccinePower(), total)) {
            this._vaccineReq.setText(ViewUtil.colorNumberAfterChar(c, this._vaccineReq.getText(), y));
        }
        this._dataReq.setText(this.attributeInfoToString(this._selectInfo.getDataPower()[0]) + (this._selectInfo.getDataPower()[1].getKey() != Enum.Condition.None ? " | " + this.attributeInfoToString(this._selectInfo.getDataPower()[1]) : ""));
        if (this.changeColor(check, this._dataReq.getText()) && evol.testAttribute(this._selectInfo.getDataPower()[0], this._digimon.getDataPower(), total) && evol.testAttribute(this._selectInfo.getDataPower()[1], this._digimon.getDataPower(), total)) {
            this._dataReq.setText(ViewUtil.colorNumberAfterChar(c, this._dataReq.getText(), y));
        }
        this._virusReq.setText(this.attributeInfoToString(this._selectInfo.getVirusPower()[0]) + (this._selectInfo.getVirusPower()[1].getKey() != Enum.Condition.None ? " | " + this.attributeInfoToString(this._selectInfo.getVirusPower()[1]) : ""));
        if (this.changeColor(check, this._virusReq.getText()) && evol.testAttribute(this._selectInfo.getVirusPower()[0], this._digimon.getVirusPower(), total) && evol.testAttribute(this._selectInfo.getVirusPower()[1], this._digimon.getVirusPower(), total)) {
            this._virusReq.setText(ViewUtil.colorNumberAfterChar(c, this._virusReq.getText(), y));
        }
        this.checkWeight(check, evol);
        this._mistakeReq.setText(this.evoInfoToString(this._selectInfo.getMistakes()));
        if (this.changeColor(check, this._mistakeReq.getText()) && evol.testEvol(this._selectInfo.getMistakes(), this._digimon.getMistake())) {
            this._mistakeReq.setText(ViewUtil.colorNumberAfterChar(c, this._mistakeReq.getText(), y));
        }
        String temp = "";
        String temp2 = "--";
        if (this._selectInfo.getTempReq() != null) {
            if (this._selectInfo.getTempReq()[0] < this._selectInfo.getTempReq()[1] && this._selectInfo.getTempReq()[0] != this._selectInfo.getTempReq()[1]) {
                temp = this._selectInfo.getTempReq()[0] + " - ";
                temp2 = "" + this._selectInfo.getTempReq()[1];
            } else if (this._selectInfo.getTempReq()[0] == this._selectInfo.getTempReq()[1]) {
                temp2 = "";
                temp = this._selectInfo.getTempReq()[0] + "";
            }
        }
        this._tempReq.setVisible(true);
        this._tempReq.setText(temp + temp2);
        if (this.changeColor(check, this._tempReq.getText()) && evol.checkTempReq(this._digimon, this._selectInfo)) {
            this._tempReq.setText(ViewUtil.colorNumberAfterChar(null, this._tempReq.getText(), y));
        }
        this._overeatReq.setText(this.evoInfoToString(this._selectInfo.getOvereat()));
        if (this.changeColor(check, this._overeatReq.getText()) && evol.testEvol(this._selectInfo.getOvereat(), this._digimon.getOvereat())) {
            this._overeatReq.setText(ViewUtil.colorNumberAfterChar(c, this._overeatReq.getText(), y));
        }
        this._disturbReq.setText(this.evoInfoToString(this._selectInfo.getDisturb()));
        if (this.changeColor(check, this._disturbReq.getText()) && evol.testEvol(this._selectInfo.getDisturb(), this._digimon.getDisturb())) {
            this._disturbReq.setText(ViewUtil.colorNumberAfterChar(c, this._disturbReq.getText(), y));
        }
        this._sickReq.setText(this.evoInfoToString(this._selectInfo.getSick()));
        if (this.changeColor(check, this._sickReq.getText()) && evol.testEvol(this._selectInfo.getSick(), this._digimon.getSickCount())) {
            this._sickReq.setText(ViewUtil.colorNumberAfterChar(c, this._sickReq.getText(), y));
        }
        this._injReq.setText(this.evoInfoToString(this._selectInfo.getInjured()));
        if (this.changeColor(check, this._injReq.getText()) && evol.testEvol(this._selectInfo.getInjured(), this._digimon.getInjCount())) {
            this._injReq.setText(ViewUtil.colorNumberAfterChar(c, this._injReq.getText(), y));
        }
        this._winReq.setText(this.evoInfoToString(this._selectInfo.getWins()) + (this._selectInfo.getWins().getValue() > 0 ? "%" : ""));
        int winRate = (int)((double)this._digimon.getWins() / (double)this._digimon.getBattles() * 100.0);
        if (this.changeColor(check, this._winReq.getText()) && evol.testEvol(this._selectInfo.getWins(), winRate)) {
            this._winReq.setText(ViewUtil.colorNumberAfterChar(c, this._winReq.getText(), y));
        }
        this._battleReq.setText(this.evoInfoToString(this._selectInfo.getBattles()));
        if (this.changeColor(check, this._battleReq.getText()) && evol.testEvol(this._selectInfo.getBattles(), this._digimon.getBattles())) {
            this._battleReq.setText(ViewUtil.colorNumberAfterChar(c, this._battleReq.getText(), y));
        }
        this._obedienceReq.setText(this.evoInfoToString(this._selectInfo.getObedience()));
        if (this.changeColor(check, this._obedienceReq.getText()) && evol.checkObedienceReq(this._digimon, this._selectInfo)) {
            this._obedienceReq.setText(ViewUtil.colorNumberAfterChar(c, this._obedienceReq.getText(), y));
        }
        if (this._selectInfo.getLevelFought() == 0) {
            this._levelReq.setText(" --");
        } else {
            this._levelReq.setText(this.evoInfoToString(this._selectInfo.getLevelFoughtCondition()));
            String s = "<b>LV " + this._selectInfo.getLevelFought() + " </b>";
            if (this.changeColor(check, this._levelReq.getText()) && evol.testEvol(this._selectInfo.getLevelFoughtCondition(), this._digimon.getLevelFought(this._selectInfo.getLevelFought()))) {
                this._levelReq.setText(ViewUtil.colorNumberAfterChar(c, this._levelReq.getText(), y));
                this._levelReq.setText(this._levelReq.getText().replace("<html>", "<html>" + s));
            } else {
                this._levelReq.setText("<html>" + s + this._levelReq.getText() + "</html>");
            }
        }
        this._incarnationReq.setText(this.evoInfoToString(this._selectInfo.getIncarnations()));
        if (this.changeColor(check, this._incarnationReq.getText()) && evol.testEvol(this._selectInfo.getIncarnations(), this._digimon.getGenerationHistory().size())) {
            this._incarnationReq.setText(ViewUtil.colorNumberAfterChar(c, this._incarnationReq.getText(), y));
        }
        if (!this._selectInfo.getMajorFood().equals((Object)Enum.Food.None)) {
            this._foodReq.setLoc(394, 359);
            this._foodReq.setText("");
            i = this.getFoodIcon(this._selectInfo.getMajorFood());
            if (check && this._selectInfo.getMajorFood() != this._digimon.getMajorFood()) {
                i = ViewUtil.getTransparentImage(i, ViewConfig._unfulfilledReqOpacity);
            }
            this._foodReq.setIcon(i);
        } else {
            this._foodReq.setLoc(404, this._overeatReq.getLocY() / this._scale);
            this._foodReq.setText("--");
            this._foodReq.removeIcon();
        }
        if (this._selectInfo.getXAntibody() == Enum.XAntibody.Induced) {
            i = this._xAntibodyReq.getAltSprite("xAntibodyReq");
            if (check && this._digimon.getXAntibodyState() == Enum.XAntibodyState.None) {
                i = ViewUtil.getTransparentImage(i, ViewConfig._unfulfilledReqOpacity);
            }
            this._xAntibodyReq.setIcon(i);
        } else {
            this._xAntibodyReq.setAltIcon("xAntibodyNoReq");
        }
        String hName = "None";
        if (this._selectInfo.getHabitat() != -1) {
            Habitat h = this._habitats.get(this._selectInfo.getHabitat());
            hName = h.getName();
            this._habitatReq.setLocX(401);
            BufferedImage sheet = ViewUtil.getResource(this.MOD_FOLDER, this.RESOURCES_FOLDER, h.getFileName());
            int i2 = 2 + ViewConfig._habitatDimensions[1];
            if (i2 > sheet.getHeight()) {
                i2 = 0;
            }
            sheet = sheet.getSubimage(0, i2, ViewConfig._habitatDimensions[0], ViewConfig._habitatDimensions[1]);
            this._habitat.setIcon(ViewUtil.resizeImage(sheet, (double)this._scale * 0.25));
            this._habitat.setBorder(BorderFactory.createLineBorder(Color.BLACK, 2 * this._scale));
        } else {
            this._habitat.removeIcon();
            this._habitat.setBorder(null);
            this._habitatReq.setLocX(375);
        }
        this._habitatReq.setText(hName.equals("None") ? "--" : hName);
        if (this.changeColor(check, this._habitatReq.getText()) && evol.checkHabitatReq(this._digimon, this._selectInfo)) {
            this._habitatReq.setText(ViewUtil.colorNumberAfterChar(c, this._habitatReq.getText(), y));
        }
        this.checkTime(check);
        this.checkField();
        this.checkMood(check, c, y);
        this.checkAttribute();
        if (priority > 0.0) {
            this._priority.setLoc(this._elementLabel.getX() / this._scale + this._elementLabel.getWidth() / this._scale + 3, this._fieldLabel.getY() / this._scale);
            this._priorityLabel.setLoc(this._priority.getX() / this._scale + this._priority.getWidth() / this._scale + 2, 2 + this._priority.getY() / this._scale);
            this._priorityLabel.setText("" + (int)(priority * ViewConfig._priorityDisplayCoefficient));
            this._priorityLabel.setVisible(true);
            this._priority.setVisible(true);
        } else {
            this._priority.setVisible(false);
            this._priorityLabel.setVisible(false);
        }
        if (check && Config._enableDNAReqReplacement && dna) {
            y = ViewConfig._allDNAFulfilledColor;
        }
        this._virusBusterReq.setText(this.evoInfoToString(this._selectInfo.getVirusBuster()) + (this._selectInfo.getVirusBuster().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._virusBusterReq.getText()) && evol.testEvol(this._selectInfo.getVirusBuster(), this._digimon.getDNA().getPercent(Enum.Field.VirusBuster))) {
            this._virusBusterReq.setText(ViewUtil.colorNumberAfterChar(c, this._virusBusterReq.getText(), y));
        }
        this._jungleTrooperReq.setText(this.evoInfoToString(this._selectInfo.getJungleTrooper()) + (this._selectInfo.getJungleTrooper().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._jungleTrooperReq.getText()) && evol.testEvol(this._selectInfo.getJungleTrooper(), this._digimon.getDNA().getPercent(Enum.Field.JungleTrooper))) {
            this._jungleTrooperReq.setText(ViewUtil.colorNumberAfterChar(c, this._jungleTrooperReq.getText(), y));
        }
        this._windGuardianReq.setText(this.evoInfoToString(this._selectInfo.getWindGuardian()) + (this._selectInfo.getWindGuardian().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._windGuardianReq.getText()) && evol.testEvol(this._selectInfo.getWindGuardian(), this._digimon.getDNA().getPercent(Enum.Field.WindGuardian))) {
            this._windGuardianReq.setText(ViewUtil.colorNumberAfterChar(c, this._windGuardianReq.getText(), y));
        }
        this._noneReq.setText(this.evoInfoToString(this._selectInfo.getNone()) + (this._selectInfo.getNone().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._noneReq.getText()) && evol.testEvol(this._selectInfo.getNone(), this._digimon.getDNA().getPercent(Enum.Field.None))) {
            this._noneReq.setText(ViewUtil.colorNumberAfterChar(c, this._noneReq.getText(), y));
        }
        this._dragonsRoarReq.setText(this.evoInfoToString(this._selectInfo.getDragonsRoar()) + (this._selectInfo.getDragonsRoar().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._dragonsRoarReq.getText()) && evol.testEvol(this._selectInfo.getDragonsRoar(), this._digimon.getDNA().getPercent(Enum.Field.DragonsRoar))) {
            this._dragonsRoarReq.setText(ViewUtil.colorNumberAfterChar(c, this._dragonsRoarReq.getText(), y));
        }
        this._nightmareSoldierReq.setText(this.evoInfoToString(this._selectInfo.getNightmareSoldier()) + (this._selectInfo.getNightmareSoldier().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._nightmareSoldierReq.getText()) && evol.testEvol(this._selectInfo.getNightmareSoldier(), this._digimon.getDNA().getPercent(Enum.Field.NightmareSoldier))) {
            this._nightmareSoldierReq.setText(ViewUtil.colorNumberAfterChar(c, this._nightmareSoldierReq.getText(), y));
        }
        this._darkAreaReq.setText(this.evoInfoToString(this._selectInfo.getDarkArea()) + (this._selectInfo.getDarkArea().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._darkAreaReq.getText()) && evol.testEvol(this._selectInfo.getDarkArea(), this._digimon.getDNA().getPercent(Enum.Field.DarkArea))) {
            this._darkAreaReq.setText(ViewUtil.colorNumberAfterChar(c, this._darkAreaReq.getText(), y));
        }
        this._natureSpiritReq.setText(this.evoInfoToString(this._selectInfo.getNatureSpirit()) + (this._selectInfo.getNatureSpirit().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._natureSpiritReq.getText()) && evol.testEvol(this._selectInfo.getNatureSpirit(), this._digimon.getDNA().getPercent(Enum.Field.NatureSpirit))) {
            this._natureSpiritReq.setText(ViewUtil.colorNumberAfterChar(c, this._natureSpiritReq.getText(), y));
        }
        this._deepSaverReq.setText(this.evoInfoToString(this._selectInfo.getDeepSea()) + (this._selectInfo.getDeepSea().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._deepSaverReq.getText()) && evol.testEvol(this._selectInfo.getDeepSea(), this._digimon.getDNA().getPercent(Enum.Field.DeepSaver))) {
            this._deepSaverReq.setText(ViewUtil.colorNumberAfterChar(c, this._deepSaverReq.getText(), y));
        }
        this._metalEmpireReq.setText(this.evoInfoToString(this._selectInfo.getMetalEmpire()) + (this._selectInfo.getMetalEmpire().getKey().toString().equals("None") ? "" : "%"));
        if (this.changeColor(check, this._metalEmpireReq.getText()) && evol.testEvol(this._selectInfo.getMetalEmpire(), this._digimon.getDNA().getPercent(Enum.Field.MetalEmpire))) {
            this._metalEmpireReq.setText(ViewUtil.colorNumberAfterChar(c, this._metalEmpireReq.getText(), y));
        }
    }

    private void checkMood(boolean check, char[] c, String y) {
        Enum.Mood mood = this._selectInfo.getMood();
        Icon i = null;
        switch (mood) {
            case Happy: {
                i = this._moodReq.getAltSprite("happy");
                this._moodReq.setText("");
                break;
            }
            case Neutral: {
                this._moodReq.removeIcon();
                this._moodReq.setText(" . . . ");
                break;
            }
            case Unhappy: {
                i = this._moodReq.getAltSprite("unhappy");
                this._moodReq.setText("");
                break;
            }
            case Depressed: {
                this._moodReq.removeIcon();
                this._moodReq.setText(" x");
                break;
            }
            case None: {
                this._moodReq.removeIcon();
                this._moodReq.setText("--");
                break;
            }
            default: {
                throw new AssertionError((Object)mood.name());
            }
        }
        if (this.changeColor(check, this._moodReq.getText())) {
            if (!this._digimon.getEvolution().checkMoodReq(this._digimon, this._selectInfo)) {
                if (i != null) {
                    i = ViewUtil.getTransparentImage(i, ViewConfig._unfulfilledReqOpacity);
                }
            } else if (i == null) {
                this._moodReq.setText(ViewUtil.colorNumberAfterChar(c, this._moodReq.getText(), y));
            }
        }
        if (i != null) {
            this._moodReq.setIcon(i);
        }
    }

    private void checkTime(boolean check) {
        Icon i = null;
        this._timeReq.setLocY(450);
        switch (this._selectInfo.getTime()) {
            case Morning: {
                i = this._timeReq.getAltSprite("morning");
                break;
            }
            case Noon: {
                i = this._timeReq.getAltSprite("noon");
                break;
            }
            case Night: {
                i = this._timeReq.getAltSprite("night");
                this._timeReq.setLocY(448);
                break;
            }
            default: {
                this._timeReq.setText("--");
                this._timeReq.removeIcon();
            }
        }
        if (i != null) {
            if (check && !this._selectInfo.getTime().equals((Object)this._digimon.getTrainTime())) {
                i = ViewUtil.getTransparentImage(i, ViewConfig._unfulfilledReqOpacity);
            }
            this._timeReq.setIcon(i);
        }
    }

    private void checkWeight(boolean check, Evolution evol) {
        this._weightReq.setLoc(347, 359);
        Icon i = null;
        this._weightReq.setText("");
        switch (this._selectInfo.getWeight()) {
            case Over: {
                i = this._weightReq.getAltSprite("weightOver");
                break;
            }
            case Healthy: {
                i = this._weightReq.getAltSprite("weightNormal");
                break;
            }
            case Under: {
                i = this._weightReq.getAltSprite("weightUnder");
                break;
            }
            default: {
                this._weightReq.setLoc(352, this._overeatReq.getLocY() / this._scale);
                this._weightReq.setText("--");
                this._weightReq.removeIcon();
            }
        }
        if (i != null) {
            if (check && !evol.checkWeightReq(this._digimon, this._selectInfo)) {
                i = ViewUtil.getTransparentImage(i, ViewConfig._unfulfilledReqOpacity);
            }
            this._weightReq.setIcon(i);
        }
    }

    private void checkField() {
        if (this._selectInfo.getUnlocked() || Config._evolHint) {
            switch (this._selectInfo.getNewField()) {
                case DragonsRoar: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[2]);
                    break;
                }
                case DeepSaver: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[4]);
                    break;
                }
                case JungleTrooper: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[3]);
                    break;
                }
                case MetalEmpire: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[1]);
                    break;
                }
                case NatureSpirit: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[7]);
                    break;
                }
                case WindGuardian: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[6]);
                    break;
                }
                case NightmareSoldier: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[5]);
                    break;
                }
                case DarkArea: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[8]);
                    break;
                }
                case VirusBuster: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[0]);
                    break;
                }
                default: {
                    this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[9]);
                    break;
                }
            }
        } else {
            this._fieldLabel.setIcon(this._fieldLabel.getSpriteSheet()[9]);
        }
    }

    private void checkAttribute() {
        if (this._selectInfo.getUnlocked() || Config._evolHint) {
            this._attributeLabel.setVisible(true);
            switch (this._selectInfo.getNewAttribute()) {
                case None: {
                    this._attributeLabel.setIcon(ViewUtil.resizeImage(this._null, 0.5));
                    break;
                }
                case Vaccine: {
                    this._attributeLabel.setAltIcon("red");
                    break;
                }
                case Data: {
                    this._attributeLabel.setAltIcon("green");
                    break;
                }
                case Virus: {
                    this._attributeLabel.setAltIcon("yellow");
                }
            }
        } else {
            this._attributeLabel.setVisible(false);
        }
    }

    private void checkElement() {
        if (this._selectInfo.getUnlocked() || Config._evolHint) {
            this._elementLabel.setLocX(this._fieldLabel.getLocX() / this._scale + this._fieldLabel.getSizeX() / this._scale + 3);
            this._elementLabel.setLocY(this._fieldLabel.getLocY() / this._scale - 1);
            this._elementLabel.setSizeX(15);
            this._elementLabel.setVisible(true);
            switch (this._selectInfo.getNewElement()) {
                case None: {
                    this._elementLabel.moveRight(2);
                    this._elementLabel.moveDown(2);
                    this._elementLabel.setIcon(ViewUtil.resizeImage(this._null, 0.5));
                    break;
                }
                case Fire: {
                    this._elementLabel.drawNumMirror(0, false);
                    break;
                }
                case Light: {
                    this._elementLabel.drawNumMirror(1, false);
                    break;
                }
                case Ice: {
                    this._elementLabel.drawNumMirror(2, false);
                    break;
                }
                case Wind: {
                    this._elementLabel.drawNumMirror(3, false);
                    break;
                }
                case Thunder: {
                    this._elementLabel.drawNumMirror(4, false);
                    break;
                }
                case Earth: {
                    this._elementLabel.drawNumMirror(5, false);
                    break;
                }
                case Water: {
                    this._elementLabel.drawNumMirror(6, false);
                    break;
                }
                case Wood: {
                    this._elementLabel.drawNumMirror(7, false);
                    break;
                }
                case Metal: {
                    this._elementLabel.setSizeX(22);
                    this._elementLabel.drawNumMirror(8, false);
                    break;
                }
                case Dark: {
                    this._elementLabel.drawNumMirror(9, false);
                }
            }
        } else {
            this._elementLabel.setVisible(false);
        }
    }

    private void populateHistory() {
        boolean cycleUp;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        int max = digimon.getEvolHistory().size();
        boolean cycleDown = this._historyPage + this._evolHistory.length < max;
        boolean bl = cycleUp = this._historyPage - 1 >= 0;
        if (cycleDown) {
            this._historyDownButton.setVisible(true);
        } else {
            this._historyDownButton.setVisible(false);
        }
        if (cycleUp) {
            this._historyUpButton.setVisible(true);
        } else {
            this._historyUpButton.setVisible(false);
        }
        this.drawEvolHistory(this._evolHistory.length);
        if (max > this._evolHistory.length) {
            max = this._evolHistory.length;
        }
        for (int i = this._historyPage; i < this._historyPage + max; ++i) {
            EvolutionInfo history = this.getDigimon(digimon.getEvolHistory().get(i)[0]);
            if (history == null) continue;
            Icon icon = this.getEvolutionInfoIcon(history);
            this._evolHistory[i - this._historyPage].setIcon(icon);
        }
    }

    private Icon getEvolutionInfoIcon(EvolutionInfo i) {
        return this.getIndividualIcon(i.getNewStage(), i.getNewSpriteSet(), this._reducedScale, i.getNewSpriteNum(), 0, 48, 48, 12);
    }

    private void restoreOriginalCollapsedIcon() {
        EvolutionInfo e = this.getCurrentCollapsedDigimon();
        if (e != null) {
            this._lastEvolButtonPressed.setIcon(this.getEvolutionInfoIcon(e));
        }
    }

    private EvolutionInfo getCurrentCollapsedDigimon() {
        if (!this._collapsed.isEmpty() && this._collapsed.get(this._collapsePage).getUnlocked()) {
            return this._collapsed.get(this._collapsePage);
        }
        return null;
    }

    public void populateEvolutions(ArrayList<EvolutionInfo> evols, SpriteObj[] evolutions, int page) {
        for (int i = 0; i < evolutions.length; ++i) {
            evolutions[i].setVisible(false);
            evolutions[i].setIcon(this._locked);
        }
        int startIndex = page * 10;
        if (startIndex >= evols.size()) {
            startIndex = 0;
        }
        for (int i = 0; i < (evols.size() > 10 ? 10 : evols.size()); ++i) {
            if (startIndex >= evols.size() || evols.get(startIndex) == null) continue;
            EvolutionInfo character = evols.get(startIndex);
            if (evols.get(startIndex).getUnlocked()) {
                Icon icon = this.getEvolutionInfoIcon(character);
                evolutions[i].setIcon(icon);
            }
            evolutions[i].setVisible(true);
            ++startIndex;
        }
    }

    private void populateGeneration() {
        int i;
        for (i = 0; i < this._evolEvolutions.length; ++i) {
            this._evolEvolutions[i].setVisible(false);
        }
        for (i = 0; i < this._evolPreEvolutions.length; ++i) {
            this._evolPreEvolutions[i].setVisible(false);
        }
        ArrayList<int[]> history = this._digimon.getGenerationHistory().get(this._preEvolutionsPage);
        EvolutionInfo character = this.getDigimon(history.get(0)[0]);
        Icon icon = this.getEvolutionInfoIcon(character);
        this._currentDigimon.setIcon(icon);
        this._currentDigimon.setVisible(true);
        this._generationAge.setText("Age " + history.get(1)[0]);
        if (this._digimon.getGenerationHistory().size() > this._preEvolutionsPage + 1) {
            history = this._digimon.getGenerationHistory().get(this._preEvolutionsPage + 1);
            character = this.getDigimon(history.get(0)[0]);
            icon = this.getEvolutionInfoIcon(character);
            this._evolPreEvolutions[8].setIcon(icon);
            this._evolPreEvolutions[8].setVisible(true);
        }
        if (this._preEvolutionsPage - 1 >= 0) {
            history = this._digimon.getGenerationHistory().get(this._preEvolutionsPage - 1);
            character = this.getDigimon(history.get(0)[0]);
            icon = this.getEvolutionInfoIcon(character);
            this._evolPreEvolutions[0].setIcon(icon);
            this._evolPreEvolutions[0].setVisible(true);
        }
        this._rightButton.setVisible(this._generationPage + 8 < (history = this._digimon.getGenerationHistory().get(this._preEvolutionsPage)).size());
        this._leftButton.setVisible(this._generationPage > 0);
        for (int i2 = 2 + this._generationPage; i2 < 8 + this._generationPage; ++i2) {
            if (history.size() <= i2) continue;
            character = this.getDigimon(history.get(i2)[0]);
            icon = this.getEvolutionInfoIcon(character);
            SpriteObj o = this._evolPreEvolutions[i2 - 1 - this._generationPage];
            if (history.get(i2)[1] >= 0) {
                EvolutionInfo partner = this.getDigimon(history.get(i2)[1]);
                Icon p = this.getEvolutionInfoIcon(partner);
                this.addJogressIcon(o, p, icon);
            } else {
                o.setLocY(217);
                o.setSize(32, 32);
                o.setIcon(icon);
            }
            o.setVisible(true);
        }
        ArrayList<Component> array = new ArrayList<Component>();
        this.addIfVisible(array, this._evolPreEvolutions[0]);
        this.addIfVisible(array, this._evolPreEvolutions[8]);
        this.addIfVisible(array, this._leftButton);
        this.addIfVisible(array, this._rightButton);
        if (this._page != Page.Req.ordinal()) {
            array.add(this._reqTab);
        }
        if (this._page != Page.DNA.ordinal()) {
            array.add(this._bonusTab);
        }
        if (this._page != Page.Jogress.ordinal() && this._selectInfo.getSpecialEvol() == Enum.SpecialEvolution.Jogress) {
            array.add(this._jogressTab);
        }
        array.add(this._generationButton);
        this.addIfVisible(array, this._historyUpButton);
        this.addIfVisible(array, this._historyDownButton);
        array.add(this._closeButton);
        this._generationButton.setAltIcon("tGenerationHistory");
        this._keyboard.setCursorPosition(-1);
        this._keyboard.addInteractiveButtons(array.toArray(new SpriteObj[array.size()]));
    }

    private Icon getIndividualIcon(Enum.Stage info, int spriteSet, double scale, int spriteNum, int row, int width, int height, int emptyPixels) {
        String spriteLoc = "sprites" + (Object)((Object)info) + spriteSet + ".png";
        if (info == Enum.Stage.Egg) {
            emptyPixels = 6;
        }
        return ViewUtil.getIndividualIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, spriteLoc, scale, spriteNum, row, width, height, emptyPixels);
    }

    private EvolutionInfo getDigimon(int index) {
        return this._controller.getModel().getDigimon().getEvolution().getDigimon(index);
    }

    private EvolutionInfo getDigimon(String s) {
        return this._controller.getModel().getDigimon().getEvolution().getDigimon(s);
    }

    private boolean selectDigimon(int index, boolean isEvolution) {
        return this.selectDigimon(index, isEvolution, false, true);
    }

    private boolean selectDigimon(int index, boolean isEvolution, boolean selectIndex, boolean checkCollapsed) {
        EvolutionInfo previousDigimon = this._selectInfo;
        if (!this._generationMode) {
            this._selectInfo = !selectIndex ? (isEvolution ? this._currentInfo.getVisibleEvolutions(this._lastDigimon).get(index) : this._currentInfo.getVisiblePreEvolutions(this._lastDigimon).get(index)) : this.getDigimon(index);
        } else {
            this._selectInfo = this.getDigimon(this._digimon.getGenerationHistory().get(index).get(0)[0]);
            this._preEvolutionsPage = index;
            this.drawEvolutionMenu();
        }
        if (!this._generationMode && (this._selectInfo.getUnlocked() || Config._evolHint)) {
            if (this._selectInfo.equals(previousDigimon)) {
                this._lastDigimon = this._currentInfo;
                if (this._selectInfo.getIsNatural()) {
                    ArrayList<EvolutionInfo> evolDigimon = this._controller.getModel().getDigimon().getEvolution().getEvolDigimon();
                    for (EvolutionInfo evol : evolDigimon) {
                        if (!this._selectInfo.getName().equals(evol.getName()) || evol.getIsNatural()) continue;
                        this._selectInfo = evol;
                        break;
                    }
                }
                if (!this._collapsed.isEmpty() && this._collapsed.contains(this._selectInfo)) {
                    this._selectInfo = this._collapsed.get(this._collapsePage);
                }
                this.checkDuplicates();
                this._collapsed.clear();
                this._currentInfo = this._selectInfo;
                this._searchBar.setText(this.getCurrentSearchString());
                if (!selectIndex) {
                    if (isEvolution) {
                        int i = index - 10 * this._evolutionsPage;
                        this._evolPreEvolutions[index >= this._evolEvolutions.length ? i : index].setVisible(true);
                    } else {
                        int i = index - 10 * this._preEvolutionsPage;
                        this._evolPreEvolutions[index >= this._evolPreEvolutions.length ? i : index].setVisible(true);
                    }
                }
                this._evolutionsPage = 0;
                this._preEvolutionsPage = 0;
                this._border.setVisible(false);
                this._keyboard.setCursorPosition(-1);
                this.drawEvolutionMenu();
            } else {
                this.setPage(0);
                if (checkCollapsed) {
                    this.processCollapsed(isEvolution);
                } else {
                    this._collapsePage = 0;
                    this._collapsed.clear();
                }
                this.populateReqs();
            }
            return true;
        }
        return false;
    }

    private boolean selectDigimon(EvolutionInfo i) {
        return this.selectDigimon(i, true);
    }

    private boolean selectDigimon(EvolutionInfo i, boolean checkCollapsed) {
        if (i != null) {
            return this.selectDigimon(i.getIndex(), false, true, checkCollapsed);
        }
        return false;
    }

    private boolean selectDigimon(int index) {
        return this.selectDigimon(this.getDigimon(index));
    }

    private boolean selectDigimon(String s) {
        return this.selectDigimon(this.getDigimon(s).getIndex());
    }

    private void checkDuplicates() {
        if (!this._selectInfo.getName().equals(this._currentInfo.getName())) {
            this.processDuplicates();
        }
    }

    private void checkRepeat(ArrayList<EvolutionInfo> list, boolean isEvolution) {
        for (EvolutionInfo e : list) {
            if (e.getCollapse() == null || e.getCollapse().isEmpty() || e.getIsNatural() || !(isEvolution ? !e.getHiddenEvolution() : !e.getHiddenPreEvolution()) || !e.getName().equals(this._selectInfo.getName()) || !e.getCollapse().contains(this._selectInfo.getIndex())) continue;
            this._collapsed.add(e);
        }
        if (!this._collapsed.isEmpty()) {
            this._collapsed.add(this._selectInfo);
            Collections.sort(this._collapsed, Comparator.comparing(EvolutionInfo::getIndex, Comparator.naturalOrder()));
        }
    }

    private void processCollapsed(boolean isEvolution) {
        this._collapsePage = 0;
        this._collapsed.clear();
        if (!isEvolution) {
            this.checkRepeat(this._currentInfo.getPreEvolutions(), isEvolution);
        } else {
            this.checkRepeat(this._currentInfo.getEvolutions(), isEvolution);
        }
        this.checkCollapsePage();
    }

    private void checkCollapsePage() {
        if (this._collapsed.size() > 0) {
            for (int i = 0; i < this._collapsed.size(); ++i) {
                if (!this._collapsed.get(i).equals(this._selectInfo)) continue;
                this._collapsePage = i;
                break;
            }
        }
    }

    private void processDuplicates() {
        this._duplicatePage = 0;
        this._duplicates.clear();
        for (EvolutionInfo e : this._digimon.getEvolution().getEvolDigimon()) {
            if (!e.getUnlocked() || e.getIsNatural() || !e.getName().equals(this._selectInfo.getName())) continue;
            this._duplicates.add(e);
        }
        if (this._duplicates.size() > 0) {
            Collections.sort(this._duplicates, Comparator.comparing(EvolutionInfo::isListPriority, Comparator.reverseOrder()));
            for (int i = 0; i < this._duplicates.size(); ++i) {
                if (this._duplicates.get(i) != this._selectInfo) continue;
                this._duplicatePage = i;
            }
        }
    }

    private String attributeInfoToString(Map.Entry<Enum.Condition, Double> entry) {
        String req;
        Enum.Condition condition = entry.getKey();
        double value = entry.getValue();
        if (value < 1.0 && value > 0.0) {
            AbstractMap.SimpleEntry<Enum.Condition, Integer> e = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(condition, (int)(value * 100.0));
            req = this.evoInfoToString(e) + "%";
        } else {
            AbstractMap.SimpleEntry<Enum.Condition, Integer> e = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(condition, (int)value);
            req = this.evoInfoToString(e);
        }
        return req;
    }

    private String conditionToString(Enum.Condition condition) {
        switch (condition) {
            case LessThan: {
                return "< ";
            }
            case EqualTo: {
                return "= ";
            }
            case GreaterThan: {
                return "> ";
            }
        }
        return "";
    }

    private String evoInfoToString(Map.Entry<Enum.Condition, Integer> entry) {
        String req = "--";
        Enum.Condition condition = entry.getKey();
        if (condition != Enum.Condition.None) {
            req = this.conditionToString(condition) + entry.getValue();
        }
        return req;
    }

    private void drawEvolHistory(int max) {
        for (int i = 0; i < this._evolHistory.length; ++i) {
            this._evolHistory[i].setVisible(false);
        }
        if (max > this._evolHistory.length) {
            max = this._evolHistory.length;
        }
        int upPad = this._historyUpButton.isVisible() ? 0 : 8 + this._historyUpButton.getSizeY() / this._scale;
        int downPad = !this._historyDownButton.isVisible() ? 10 + this._historyDownButton.getSizeY() / this._scale : 0;
        int totalPad = (220 + downPad + upPad) / max;
        this._evolHistory[0].setLoc(477, 59 - upPad);
        this._evolHistory[0].setVisible(true);
        for (int i = 1; i < max; ++i) {
            this._evolHistory[i].setLoc(this._evolHistory[0].getLocX() / this._scale, this._evolHistory[i - 1].getLocY() / this._scale + totalPad);
            this._evolHistory[i].setVisible(true);
        }
        this._historyUpButton.setLoc(this._evolHistory[0].getLocX() / this._scale + 3, this._evolHistory[0].getLocY() / this._scale - this._historyUpButton.getSizeY() / this._scale - 6);
        this._historyDownButton.setLoc(this._historyUpButton.getLocX() / this._scale, this._evolHistory[max - 1].getLocY() / this._scale + this._evolHistory[max - 1].getSizeY() / this._scale + 6);
    }

    private void setDefaultLoc() {
        this._evolPreEvolutions[1].setLoc(158, 176);
        this._evolPreEvolutions[0].setLoc(158, 112);
        this._evolPreEvolutions[4].setLoc(96, 217);
        this._evolPreEvolutions[2].setLoc(96, 144);
        this._evolPreEvolutions[3].setLoc(96, 71);
        this._evolPreEvolutions[9].setLoc(31, 252);
        this._evolPreEvolutions[7].setLoc(31, 199);
        this._evolPreEvolutions[5].setLoc(31, 146);
        this._evolPreEvolutions[6].setLoc(31, 93);
        this._evolPreEvolutions[8].setLoc(31, 40);
        this._evolEvolutions[0].setLoc(274, 112);
        this._evolEvolutions[1].setLoc(274, 176);
        this._evolEvolutions[3].setLoc(336, 71);
        this._evolEvolutions[2].setLoc(336, 144);
        this._evolEvolutions[4].setLoc(336, 217);
        this._evolEvolutions[8].setLoc(401, 40);
        this._evolEvolutions[6].setLoc(401, 93);
        this._evolEvolutions[5].setLoc(401, 146);
        this._evolEvolutions[7].setLoc(401, 199);
        this._evolEvolutions[9].setLoc(401, 252);
        this._leftButton.setLoc(199, 150);
        this._rightButton.setLoc(251, 150);
    }

    private void setGenerationLoc() {
        int y = 217;
        int x = 48;
        int empty = this._evolPreEvolutions[0].getSizeX() / this._scale;
        this._evolPreEvolutions[0].setLoc(96, this._currentDigimon.getLocY() / this._scale);
        this._evolPreEvolutions[8].setLoc(336, this._currentDigimon.getLocY() / this._scale);
        this._evolPreEvolutions[1].setLoc(x, y);
        this._evolPreEvolutions[2].setLoc(x + this._evolPreEvolutions[0].getSizeX() / this._scale + empty, y);
        this._evolPreEvolutions[3].setLoc(x + this._evolPreEvolutions[0].getSizeX() / this._scale * 2 + empty * 2, y);
        this._evolPreEvolutions[4].setLoc(x + this._evolPreEvolutions[0].getSizeX() / this._scale * 3 + empty * 3, y);
        this._evolPreEvolutions[5].setLoc(x + this._evolPreEvolutions[0].getSizeX() / this._scale * 4 + empty * 4, y);
        this._evolPreEvolutions[6].setLoc(x + this._evolPreEvolutions[0].getSizeX() / this._scale * 5 + empty * 5, y);
        this._leftButton.setLoc(this._evolPreEvolutions[1].getLocX() / this._scale - this._leftButton.getSizeX() / this._scale - 6, this._evolPreEvolutions[1].getLocY() / this._scale);
        this._rightButton.setLoc(this._evolPreEvolutions[6].getLocX() / this._scale + this._evolPreEvolutions[6].getSizeX() / this._scale + 25, this._leftButton.getLocY() / this._scale);
    }

    private void drawEvolutionMenu() {
        ArrayList<Component> obj = new ArrayList<Component>();
        this._closeButton.setLocX(513);
        this._closeButton.setVisible(true);
        this._searchButton.setVisible(true);
        this._searchBar.setVisible(true);
        this._currentDigimon.setVisible(true);
        this._name.setVisible(true);
        this._selectDigimon.setVisible(true);
        this._vaccineReq.setVisible(true);
        this._dataReq.setVisible(true);
        this._virusReq.setVisible(true);
        this._weightReq.setVisible(true);
        this._mistakeReq.setVisible(true);
        this._tempReq.setVisible(true);
        this._habitatReq.setVisible(true);
        this._overeatReq.setVisible(true);
        this._disturbReq.setVisible(true);
        this._sickReq.setVisible(true);
        this._injReq.setVisible(true);
        this._battleReq.setVisible(true);
        this._winReq.setVisible(true);
        this._obedienceReq.setVisible(true);
        this._timeReq.setVisible(true);
        this._moodReq.setVisible(true);
        this._levelReq.setVisible(true);
        this._incarnationReq.setVisible(true);
        this._foodReq.setVisible(true);
        this._xAntibodyReq.setVisible(true);
        this.drawEvol();
        this._evolutionTree.setVisible(true);
        this.setupTree();
        this._reqTab.setVisible(true);
        this._bonusTab.setVisible(true);
        this.drawDNAReqs();
        this.addIfVisible(obj, this._evolPreEvolutions[8]);
        this.addIfVisible(obj, this._evolPreEvolutions[6]);
        this.addIfVisible(obj, this._evolPreEvolutions[5]);
        this.addIfVisible(obj, this._evolPreEvolutions[7]);
        this.addIfVisible(obj, this._evolPreEvolutions[9]);
        this.addIfVisible(obj, this._evolPreEvolutions[3]);
        this.addIfVisible(obj, this._evolPreEvolutions[2]);
        this.addIfVisible(obj, this._evolPreEvolutions[4]);
        this.addIfVisible(obj, this._evolPreEvolutions[0]);
        this.addIfVisible(obj, this._evolPreEvolutions[1]);
        obj.add(this._currentDigimon);
        if (!this._generationMode) {
            this._upButton.setVisible(true);
            this._downButton.setVisible(true);
            this._generationAge.setVisible(false);
            this.checkCycleButtons();
            if (this._upButton.isVisible()) {
                obj.add(this._upButton);
            }
            if (this._downButton.isVisible()) {
                obj.add(this._downButton);
            }
            if (this._leftButton.isVisible()) {
                obj.add(this._leftButton);
            }
            if (this._rightButton.isVisible()) {
                obj.add(this._rightButton);
            }
        } else {
            this._upButton.setVisible(false);
            this._downButton.setVisible(false);
            this._generationAge.setVisible(true);
        }
        this.addIfVisible(obj, this._evolEvolutions[0]);
        this.addIfVisible(obj, this._evolEvolutions[1]);
        this.addIfVisible(obj, this._evolEvolutions[3]);
        this.addIfVisible(obj, this._evolEvolutions[2]);
        this.addIfVisible(obj, this._evolEvolutions[4]);
        this.addIfVisible(obj, this._evolEvolutions[8]);
        this.addIfVisible(obj, this._evolEvolutions[6]);
        this.addIfVisible(obj, this._evolEvolutions[5]);
        this.addIfVisible(obj, this._evolEvolutions[7]);
        this.addIfVisible(obj, this._evolEvolutions[9]);
        this.addIfVisible(obj, this._collapsedRightButton);
        if (this._page != Page.Req.ordinal()) {
            obj.add(this._reqTab);
        }
        if (this._page != Page.DNA.ordinal()) {
            obj.add(this._bonusTab);
        }
        if (this._page != Page.Jogress.ordinal() && this._selectInfo.getSpecialEvol() == Enum.SpecialEvolution.Jogress) {
            obj.add(this._jogressTab);
        }
        this.addIfVisible(obj, this._jogressLeftButton);
        this.addIfVisible(obj, this._jogressRightButton);
        if (!this._digimon.getGenerationHistory().isEmpty()) {
            this._generationButton.setVisible(true);
            obj.add(this._generationButton);
        } else {
            this._generationButton.setVisible(false);
        }
        this.addIfVisible(obj, this._historyUpButton);
        for (SpriteObj o : this._evolHistory) {
            if (!o.isVisible() || o.getIcon() == null) continue;
            obj.add(o);
        }
        this.addIfVisible(obj, this._historyDownButton);
        obj.add(this._searchBar);
        obj.add(this._searchButton);
        obj.add(this._closeButton);
        this._generationButton.setAltIcon("tGenerationHistory");
        this._keyboard.setCursorPosition(-1);
        if (!this._generationMode) {
            this._keyboard.addInteractiveButtons(obj.toArray(new Component[obj.size()]));
        }
    }

    private void drawDNAReqs() {
        this._virusBusterReq.setVisible(this._page == Page.DNA.ordinal());
        this._metalEmpireReq.setVisible(this._page == Page.DNA.ordinal());
        this._dragonsRoarReq.setVisible(this._page == Page.DNA.ordinal());
        this._jungleTrooperReq.setVisible(this._page == Page.DNA.ordinal());
        this._deepSaverReq.setVisible(this._page == Page.DNA.ordinal());
        this._nightmareSoldierReq.setVisible(this._page == Page.DNA.ordinal());
        this._windGuardianReq.setVisible(this._page == Page.DNA.ordinal());
        this._natureSpiritReq.setVisible(this._page == Page.DNA.ordinal());
        this._darkAreaReq.setVisible(this._page == Page.DNA.ordinal());
        this._noneReq.setVisible(this._page == Page.DNA.ordinal());
        if (this._page == Page.Jogress.ordinal()) {
            this.drawJogressAttributeCombinations(this._selectInfo.getNewAttribute());
        }
        this._jogressLeftButton.setVisible(this._page == Page.Jogress.ordinal());
        this._jogressRightButton.setVisible(this._page == Page.Jogress.ordinal());
    }

    private void drawJogressAttributeCombinations(Enum.Attribute result) {
        ArrayList<JogressAttributePair> list = this._digimon.getAffinity().getJogressCombinations(result);
        BufferedImage full = ViewUtil.createBuffImage(this._jogressMenu.getAltSprite("evolutionTreeAttributeCombos"));
        Graphics2D g2 = full.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(Color.BLACK);
        Float size = Float.valueOf(60.0f * (float)this._scale);
        Font f = this._name.getFont().deriveFont(size.floatValue());
        g2.setFont(f);
        g2.drawImage(full, null, 0, 0);
        int rowX1 = 74 * this._scale;
        int rowX2 = 264 * this._scale;
        int rowY1 = 70 * this._scale;
        int rowY2 = 136 * this._scale;
        for (int i = 0; i < 4; ++i) {
            int index = i + 4 * this._jogressPage;
            if (index >= list.size()) continue;
            Enum.Attribute sa = list.get(index).getDigimonAttribute();
            Enum.Attribute pa = list.get(index).getPartnerAttribute();
            BufferedImage self = this.getAttributeImage(sa);
            BufferedImage partner = this.getAttributeImage(pa);
            BufferedImage evol = this.getAttributeImage(result);
            int x = 0;
            int y = 0;
            rowX1 += sa == Enum.Attribute.None ? 2 * this._scale : 0;
            rowX2 += sa == Enum.Attribute.None ? 1 * this._scale : 0;
            switch (i) {
                case 0: {
                    x = rowX1;
                    y = rowY1;
                    break;
                }
                case 1: {
                    x = rowX1;
                    y = rowY2;
                    break;
                }
                case 2: {
                    x = rowX2;
                    y = rowY1;
                    break;
                }
                case 3: {
                    x = rowX2;
                    y = rowY2;
                }
            }
            float pad = size.floatValue();
            x = this.drawAttribute(self, g2, x + 5 * this._scale + (sa == Enum.Attribute.None ? 4 * this._scale : 0), y + (sa == Enum.Attribute.None ? 2 * this._scale : 0));
            g2.drawString("+", x + self.getWidth() - 1 * this._scale + 13 * this._scale, y + 27 * this._scale);
            x = (int)((float)x + (pad + (float)(10 * this._scale) - (float)(sa == Enum.Attribute.None ? 5 * this._scale : 0)));
            x = this.drawAttribute(partner, g2, x, y + (pa == Enum.Attribute.None ? 2 * this._scale : 0));
            g2.drawString("=", x + partner.getWidth() - 4 * this._scale + 13 * this._scale, y + 28 * this._scale);
            x = (int)((float)x + pad);
            this.drawAttribute(evol, g2, x, y + (result == Enum.Attribute.None ? 2 * this._scale : 0));
        }
        this._jogressMenu.setIcon(new ImageIcon(full));
        this._jogressMenu.update(g2);
        g2.dispose();
    }

    private int drawAttribute(BufferedImage image, Graphics2D g2, int x, int y) {
        if (image != null) {
            g2.drawImage(image, null, x, y);
        } else {
            g2.drawString("NA", x, y += 27 * this._scale);
        }
        return x;
    }

    private BufferedImage getAttributeImage(Enum.Attribute a) {
        int scale = (int)(2.0 / (double)this._scale * (double)this._scale);
        BufferedImage i = null;
        switch (a) {
            case Vaccine: {
                i = ViewUtil.createBuffImage(ViewUtil.resizeImage(this._attributeLabel.getAltSprite("red"), (double)scale));
                break;
            }
            case Data: {
                i = ViewUtil.createBuffImage(ViewUtil.resizeImage(this._attributeLabel.getAltSprite("green"), (double)scale));
                break;
            }
            case Virus: {
                i = ViewUtil.createBuffImage(ViewUtil.resizeImage(this._attributeLabel.getAltSprite("yellow"), (double)scale));
                break;
            }
            case None: {
                i = ViewUtil.createBuffImage(ViewUtil.resizeImage(this._null, (double)((int)(1.5 / (double)this._scale * (double)this._scale))));
            }
        }
        return i;
    }

    private void addIfVisible(ArrayList<Component> obj, SpriteObj o) {
        if (o.isVisible()) {
            obj.add(o);
        }
    }

    private void checkCollapsed() {
        if (!this._collapsed.isEmpty() && !this._generationMode) {
            this._collapsedRightButton.setLocX(this._specialEvol.getLocX() / this._scale + 4);
            if (this._specialEvol.isVisible()) {
                this._collapsedRightButton.setLocY(this._specialEvol.getHeight() / this._scale + this._specialEvol.getLocY() / this._scale);
            } else {
                this._collapsedRightButton.setLocY(this._specialEvol.getLocY() / this._scale + 9);
            }
            this._collapsedRightButton.setVisible(true);
        } else {
            this._collapsedRightButton.setVisible(false);
        }
    }

    private void checkSpecialEvol() {
        this._specialEvol.setSize(16, 16);
        this._specialEvol.setLoc(227, 312);
        switch (this._selectInfo.getSpecialEvol()) {
            case None: 
            case Failed: {
                if (this._selectInfo.getEvolItemID() != -1) {
                    Consumable c = this._digimon.getItems().get(this._selectInfo.getEvolItemID());
                    ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, "Items", c, this._itemLabel, 1, 16, 16, 2.0 * (double)this._scale);
                    Icon icon = this._itemLabel.getSpriteSheet()[0];
                    this._specialEvol.setSize(16, 16);
                    this._specialEvol.setLoc(228, 311);
                    this._specialEvol.setIcon(icon);
                    this._specialEvol.setVisible(true);
                    break;
                }
                if (this._selectInfo.getEvolFoodID() != -1) {
                    Consumable c = this._digimon.getFoodTypes().get(this._selectInfo.getEvolFoodID());
                    ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, "Food", c, this._foodLabel, 6, 24, 24, 0.667 * (double)this._scale);
                    Icon icon = this._foodLabel.getSpriteSheet()[0];
                    this._specialEvol.setSize(16, 16);
                    this._specialEvol.setLoc(227, 311);
                    this._specialEvol.setIcon(icon);
                    this._specialEvol.setVisible(true);
                    break;
                }
                this._specialEvol.setVisible(false);
                break;
            }
            case Jogress: {
                this._specialEvol.drawNumMirror(0, false);
                break;
            }
            case Death: {
                this._specialEvol.drawNumMirror(1, false);
                break;
            }
            case Xros: {
                this._specialEvol.drawNumMirror(2, false);
                break;
            }
            case Mode: {
                this._specialEvol.drawNumMirror(3, false);
                break;
            }
            case Fusion: {
                this._specialEvol.drawNumMirror(4, false);
            }
        }
        if (this._selectInfo.getSpecialEvol() != Enum.SpecialEvolution.None && this._selectInfo.getSpecialEvol() != Enum.SpecialEvolution.Failed) {
            this._specialEvol.setVisible(true);
        }
    }

    private void drawEvol() {
        for (SpriteObj evol : this._evolHistory) {
            evol.setVisible(true);
        }
    }

    private void addJogressIcon(SpriteObj o, Icon p, Icon e) {
        BufferedImage partner = ViewUtil.createBuffImage(ViewUtil.resizeImage(p, 0.5));
        o.setLocY(208);
        o.setSize(35 + partner.getWidth(), 35 + partner.getHeight());
        BufferedImage evol = ViewUtil.createBuffImage(e);
        BufferedImage b = new BufferedImage(o.getSizeX(), o.getSizeY(), 2);
        Graphics2D g2 = b.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        g2.drawImage(evol, null, 0, 9 * this._scale);
        g2.drawImage(partner, null, evol.getWidth() + 3 * this._scale, 0);
        g2.dispose();
        o.setIcon(new ImageIcon(b));
    }

    public void checkCycleButtons() {
        int evolutions = this._currentInfo.getVisibleEvolutions(null).size();
        int preEvolutions = this._currentInfo.getVisiblePreEvolutions(null).size();
        if (evolutions > this._evolEvolutions.length || preEvolutions > this._evolPreEvolutions.length) {
            this._downButton.setVisible(true);
        } else {
            this._downButton.setVisible(false);
        }
        if (evolutions <= (this._evolutionsPage + 1) * this._evolEvolutions.length && preEvolutions <= (this._preEvolutionsPage + 1) * this._evolPreEvolutions.length) {
            this._downButton.setVisible(false);
        }
        if (this._evolutionsPage > 0 || this._preEvolutionsPage > 0) {
            this._upButton.setVisible(true);
        } else {
            this._upButton.setVisible(false);
        }
        if (this.canIncDuplicatePage()) {
            this._rightButton.setVisible(true);
        } else {
            this._rightButton.setVisible(false);
        }
        if (this.canDecDuplicatePage()) {
            this._leftButton.setVisible(true);
        } else {
            this._leftButton.setVisible(false);
        }
    }

    private boolean selectSearchDigimon(String s) {
        boolean success = false;
        if (s.contains("https://")) {
            s = s.split("net/")[1];
        }
        try {
            success = this.selectDigimon(s);
        }
        catch (NullPointerException nullPointerException) {
            // empty catch block
        }
        if (success && this._selectInfo != null && !this._selectInfo.getName().equals("Default") && this._selectInfo.getUnlocked()) {
            this.selectDigimon(s);
        } else if (!s.isEmpty()) {
            for (EvolutionInfo d : this._digimon.getEvolution().getEvolDigimon()) {
                if (!d.getUnlocked() || !d.getName().toLowerCase().contains(s.toLowerCase())) continue;
                this.selectDigimon(d.getIndex());
                this.selectDigimon(d.getIndex());
                success = true;
                break;
            }
        } else if (!this._selectInfo.getUnlocked()) {
            success = false;
            this.selectDigimon(this._currentInfo);
            this._searchBar.setText(this.getCurrentSearchString());
        }
        if (!success) {
            this._sounds.playSound(SoundConfig._error);
            this._searchBar.setText(this.getCurrentSearchString());
        } else {
            this._back.requestFocus();
            this._keyboard.setCursorPosition(-1);
            this._searchButton.removeIcon();
        }
        return success;
    }

    private String getCurrentSearchString() {
        String s = "https://www.dvpet.net/";
        String name = "???";
        if (this._currentInfo.getUnlocked()) {
            name = this._currentInfo.getName();
        }
        if (this._currentInfo != null) {
            s = s + name.toLowerCase().replace(" ", "_");
        }
        return s;
    }

    private String getStageNumeral(Enum.Stage s) {
        switch (s) {
            case Fresh: {
                return "I";
            }
            case InTraining: {
                return "II";
            }
            case Rookie: {
                return "III";
            }
            case Champion: {
                return "IV";
            }
            case Ultimate: {
                return "V";
            }
            case Mega: {
                return "VI";
            }
        }
        throw new AssertionError((Object)s.name());
    }

    private Icon getFoodIcon(Enum.Food f) {
        int i = ViewUtil.getFoodGroupNum(f);
        Consumable c = this._digimon.getFoodTypes().get(i);
        if (c != null) {
            this._foodLabel.setSpriteSheet(ViewUtil.getFoodSheet(c, this.MOD_FOLDER, this.RESOURCES_FOLDER, (double)this._scale * 1.5));
        }
        return this._foodLabel.getSpriteSheet()[0];
    }

    @Override
    public void dispose() {
        for (FocusListener focusListener : this._searchBar.getFocusListeners()) {
            this._searchBar.removeFocusListener(focusListener);
        }
        this._border = null;
        this._searchBar = null;
        this._searchButton = null;
        for (EventListener eventListener : this.getMouseListeners()) {
            this.removeMouseListener((MouseListener)eventListener);
        }
        for (EventListener eventListener : this.getMouseMotionListeners()) {
            this.removeMouseMotionListener((MouseMotionListener)eventListener);
        }
        this._digimon = null;
        this._controller = null;
        this._display.removeAll();
        this._display = null;
        this._back.removeAll();
        this._back = null;
        this._dna.removeAll();
        this._dna = null;
        this._locked = null;
        this._evolutionTree = null;
        this._closeButton = null;
        this._upButton = null;
        this._downButton = null;
        this._jogressLeftButton = null;
        this._jogressRightButton = null;
        this._currentDigimon = null;
        this._currentInfo = null;
        for (SpriteObj spriteObj : this._evolEvolutions) {
            if (spriteObj != null) {
                spriteObj.dispose();
            }
            Object var4_11 = null;
        }
        this._evolEvolutions = null;
        for (SpriteObj spriteObj : this._evolPreEvolutions) {
            if (spriteObj != null) {
                spriteObj.dispose();
            }
            Object var4_14 = null;
        }
        this._evolPreEvolutions = null;
        this._selectDigimon = null;
        this._selectInfo = null;
        this._name = null;
        this._specialEvol = null;
        this._fieldLabel = null;
        this._elementLabel = null;
        this._attributeLabel.getAltSprites().clear();
        this._attributeLabel = null;
        this._null = null;
        this._reqTab = null;
        this._bonusTab = null;
        this._jogressTab = null;
        this._vaccineReq = null;
        this._dataReq = null;
        this._virusReq = null;
        this._weightReq = null;
        this._mistakeReq = null;
        this._overeatReq = null;
        this._disturbReq = null;
        this._sickReq = null;
        this._injReq = null;
        this._battleReq = null;
        this._winReq = null;
        this._obedienceReq = null;
        this._timeReq = null;
        this._moodReq = null;
        this._tempReq = null;
        this._levelReq = null;
        this._incarnationReq = null;
        this._foodReq = null;
        this._xAntibodyReq = null;
        this._dnaMenu = null;
        this._virusBusterReq = null;
        this._metalEmpireReq = null;
        this._dragonsRoarReq = null;
        this._jungleTrooperReq = null;
        this._deepSaverReq = null;
        this._nightmareSoldierReq = null;
        this._windGuardianReq = null;
        this._natureSpiritReq = null;
        this._darkAreaReq = null;
        this._noneReq = null;
        for (SpriteObj spriteObj : this._evolHistory) {
            if (spriteObj != null) {
                spriteObj.dispose();
            }
            Object var4_17 = null;
        }
        this._evolHistory = null;
        this._generationButton = null;
        this._generationAge = null;
        this._foodLabel = null;
        this._itemLabel = null;
        this._habitats = null;
        this._duplicates.clear();
        this._collapsedRightButton = null;
        this._collapsed.clear();
        for (Component component : this.getComponents()) {
            if (component == null) continue;
            Object var4_20 = null;
        }
        this.removeAll();
        super.dispose();
    }

    public static enum Page {
        Req,
        DNA,
        Jogress;

    }
}

