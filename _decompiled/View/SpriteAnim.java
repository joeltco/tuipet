/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.ClockTic;
import Controller.Utility;
import Model.AttackEffectProcess;
import Model.Battle;
import Model.Config;
import Model.Consumable;
import Model.CrashEntry;
import Model.DNA;
import Model.Enemy;
import Model.Enum;
import Model.EvolutionInfo;
import Model.FoodType;
import Model.Habitat;
import Model.Item;
import Model.MapLevel;
import Model.PhysicalState;
import Model.ShopConsumable;
import Model.Tournament;
import Model.Town;
import Model.Trophy;
import Model.ViewSettings;
import Model.WorldMap;
import Model.Zone;
import View.BackgroundAnim;
import View.DisplayPane;
import View.JTextFieldLimit;
import View.KeyboardCursor;
import View.Polygon;
import View.Shell;
import View.SoundConfig;
import View.SoundObj;
import View.SpriteObj;
import View.ViewConfig;
import View.ViewUtil;
import View.Weather;
import java.awt.AWTException;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Component;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GraphicsEnvironment;
import java.awt.IllegalComponentStateException;
import java.awt.MouseInfo;
import java.awt.Point;
import java.awt.Robot;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collections;
import java.util.Random;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.sound.sampled.Clip;
import javax.swing.BorderFactory;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.border.Border;

public class SpriteAnim
extends JFrame {
    private final String MOD_FOLDER;
    private final String RESOURCES_FOLDER;
    private KeyboardCursor _keyboard;
    private final int[] CODE = new int[]{38, 38, 40, 40, 37, 39, 37, 39, 66};
    private int[] _strokes = new int[9];
    private DisplayPane _back = new DisplayPane(false);
    private DisplayPane _display = new DisplayPane(false);
    private DisplayPane _mainDisplay = new DisplayPane(false);
    private DisplayPane _shell = new DisplayPane(false);
    private DisplayPane _interact = new DisplayPane(false);
    private DisplayPane _menuInteract = new DisplayPane(false);
    private DisplayPane _mainInteract = new DisplayPane(false);
    private DisplayPane _overlay = new DisplayPane(false);
    private Weather _weather;
    private boolean _pauseWeather;
    private Enum.Weather _currentWeather = Enum.Weather.Clear;
    private Polygon _rect;
    private Polygon _animRect;
    private Polygon _menuRect;
    private BackgroundAnim _backgroundAnim;
    private Icon _frozen;
    private Font _bit;
    private JFrame _debugFrame;
    private JTextArea _debugText1;
    private JTextArea _debugText2;
    private ClockTic _controller;
    private ArrayList<SpriteObj> _zoneButtons = new ArrayList();
    private final int _animWinLocXMin = 27;
    private final int _animWinLocYMin = 48;
    private final int _animWinLocXMax = 105;
    private final int _animWinLocYMax = 69;
    private int _xPad = 26;
    private int _yPad = 54;
    private boolean _isLoaded = false;
    private SoundObj _sounds;
    private SpriteObj _soundLabel;
    private SpriteObj _settingsMenu;
    private SpriteObj _focusLabel;
    private SpriteObj _onTopLabel;
    private SpriteObj _smallScale;
    private SpriteObj _mediumScale;
    private SpriteObj _largeScale;
    private SpriteObj _character;
    private SpriteObj _filthLabel;
    private SpriteObj _washLabel;
    private SpriteObj _emotionLabel;
    private SpriteObj _moodLabel;
    private SpriteObj _praiseButton;
    private SpriteObj _scoldButton;
    private int _posx;
    private int _posy;
    private SpriteObj _startMenu;
    private SpriteObj _closeButton;
    private SpriteObj _startButton;
    private SpriteObj _loadButton;
    private SpriteObj _newGameMenu;
    private SpriteObj _fastClockDisplay;
    private SpriteObj _fastClockButton;
    private SpriteObj _difficultyMenu;
    private SpriteObj _timeSkipButton;
    private SpriteObj _leftButton;
    private SpriteObj _rightButton;
    private SpriteObj _upButton;
    private SpriteObj _downButton;
    private SpriteObj _eggLabel;
    private SpriteObj _colonLabel;
    private SpriteObj _plusHoursButton;
    private SpriteObj _minusHoursButton;
    private SpriteObj _plusMinutesButton;
    private SpriteObj _minusMinutesButton;
    private SpriteObj _shopHours;
    private JLabel _hoursPane;
    private JLabel _minutesPane;
    private SpriteObj _timeLabel;
    private SpriteObj _seasonLabel;
    private SpriteObj _tempLabel;
    private SpriteObj _tempBar;
    private Polygon _tempFill;
    private double _tempFillDefaultSize;
    private SpriteObj _tempArrow;
    private SpriteObj _tempMoodArrow;
    private SpriteObj _currentTemp;
    private boolean _tempDrag;
    private Polygon _adventureBar;
    private SpriteObj _enterButton;
    private JLabel _userInputTitle;
    private SpriteObj _saveLoadMenu;
    private JTextField _stringPane;
    private SpriteObj _mainBackground;
    private SpriteObj _background;
    private SpriteObj _statusButton;
    private SpriteObj _feedButton;
    private SpriteObj _digisoulButton;
    private SpriteObj _gameButton;
    private SpriteObj _battleButton;
    private SpriteObj _washButton;
    private SpriteObj _lightButton;
    private SpriteObj _firstAidButton;
    private SpriteObj _tempButton;
    private SpriteObj _callIcon;
    private SpriteObj _states;
    private byte _stateNum = 0;
    private SpriteObj _bandageState;
    private SpriteObj _medicineState;
    private SpriteObj _injuryState;
    private SpriteObj _sickState;
    private SpriteObj _vitaminState;
    private SpriteObj _fatigueState;
    private SpriteObj _teachState;
    private SpriteObj _evolutionTreeButton;
    private SpriteObj _mapButton;
    private SpriteObj _clockButton;
    private SpriteObj _settingsButton;
    private SpriteObj _saveButton;
    private SpriteObj _saveOption;
    private SpriteObj _quitOption;
    private SpriteObj _backButton;
    private SpriteObj _pauseButton;
    private SpriteObj _battlesPanel;
    private JLabel _winRatePanel;
    private SpriteObj _bitsLabel;
    private SpriteObj _bitsPanel;
    private SpriteObj _fullHunger;
    private SpriteObj _hungerLabel;
    private SpriteObj _fullExercise;
    private SpriteObj _exerciseLabel;
    private SpriteObj _rateLabel;
    private SpriteObj _rate;
    private SpriteObj _typeLabel;
    private SpriteObj _attribute;
    private SpriteObj _fieldLabel;
    private SpriteObj _elementLabel;
    private SpriteObj _weightLabel;
    private JLabel _weightPanel;
    private JLabel _agePanel;
    private SpriteObj _personLabel;
    private SpriteObj _favFoodLabel;
    private SpriteObj _favAttLabel;
    private SpriteObj _favTimeLabel;
    private SpriteObj _obedienceLabel;
    private SpriteObj _obedienceFull;
    private SpriteObj _energy;
    private SpriteObj _energyLabel;
    private SpriteObj _energyBar;
    private SpriteObj _recoveryLabel;
    private SpriteObj _sleepLabel;
    private SpriteObj _ticLabel;
    private SpriteObj _ticBar;
    private SpriteObj _meatButton;
    private SpriteObj _vegButton;
    private SpriteObj _fishButton;
    private SpriteObj _fruitButton;
    private SpriteObj _inventoryButton;
    private SpriteObj _foodShopButton;
    private SpriteObj _foodLabel;
    private SpriteObj _itemLabel;
    private FoodType _foodType;
    private Item _itemType;
    private ShopConsumable _consumableType;
    private SpriteObj _consumableDescription;
    private int _consumablePage = 0;
    private int _habitat = -1;
    private SpriteObj _battleOption;
    private SpriteObj _practiceOption;
    private SpriteObj _cardsOption;
    private SpriteObj _jogressOption;
    private SpriteObj _multiOption;
    private SpriteObj _tourneyOption;
    private SpriteObj _optionButton;
    private SpriteObj _prizeButton;
    private SpriteObj _cardShop;
    private SpriteObj _collection;
    private SpriteObj _cardButton;
    private SpriteObj _tourneyRecords;
    private SpriteObj _seasonRecords;
    private SpriteObj _springRecords;
    private SpriteObj _summerRecords;
    private SpriteObj _fallRecords;
    private SpriteObj _winterRecords;
    private SpriteObj _tourneyEnter;
    private SpriteObj[] _trophies = new SpriteObj[ViewConfig._trophyRecordsPageSize];
    private int _trophyPage = 0;
    private int _trophyInSchedule = 0;
    private SpriteObj _availableHours;
    private SpriteObj _roster;
    private SpriteObj _royaleLineup;
    private SpriteObj[] _participants;
    private SpriteObj _royaleNum;
    private SpriteObj _hostOption;
    private SpriteObj _connectOption;
    private SpriteObj _hostNameMenu;
    private SpriteObj _vaccineAttack;
    private SpriteObj _dataAttack;
    private SpriteObj _virusAttack;
    private SpriteObj _useCardButton;
    private SpriteObj _vaccinePowerLabel;
    private SpriteObj _dataPowerLabel;
    private SpriteObj _virusPowerLabel;
    private SpriteObj _attackOption;
    private SpriteObj _surrenderOption;
    private SpriteObj _yesLabel;
    private SpriteObj _noLabel;
    private SpriteObj _restartLabel;
    private SpriteObj _menuButton;
    private SpriteObj _map;
    private SpriteObj _okValidation;
    private SpriteObj _stepsLabel;
    private SpriteObj _stepsPanel;
    private SpriteObj _travelLabel;
    private SpriteObj _zoneDetail;
    private SpriteObj _townLabel;
    private SpriteObj _healthBar;
    private SpriteObj _healthBarFull;
    private SpriteObj _healthUp;
    private int _frame;
    private int _stateFrame;
    private byte _interval;
    private Enum.State _currentAnim;
    private int _animValue;
    private int _animValue2;
    private int _animValue3;
    private int _animValue4;
    private final int DIGIMEMORY_INDEX = 32;
    private String _message;
    private SpriteObj _messageDisplay;
    private SpriteObj _habitatLabel;
    private SpriteObj _itemOption;
    private SpriteObj _trainBar;
    private SpriteObj _trainBarFull;
    private SpriteObj _proteinBar;
    private SpriteObj _mineralBar;
    private SpriteObj _vitaminBar;
    private SpriteObj _hitLabel;
    private SpriteObj _hitButton;
    private SpriteObj _shieldTop;
    private SpriteObj _shieldBot;
    private SpriteObj _specialAttacks;
    private SpriteObj _attackSprite;
    private SpriteObj _battleBags;
    private SpriteObj _opponent;
    private final int _redAttackSpriteLoc = 0;
    private final int _greenAttackSpriteLoc = 25;
    private final int _yellowAttackSpriteLoc = 50;
    private SpriteObj _roomEffect;
    private SpriteObj _battleFlash;
    private SpriteObj _select;
    private JLabel _border = new JLabel(){

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D)g;
            g2.setColor(Color.BLACK);
            g2.setStroke(new BasicStroke(4 * SpriteAnim.this.getScale()));
            int length = SpriteAnim.this._border.getWidth() / 4;
            int height = SpriteAnim.this._border.getHeight() / 4;
            g2.drawLine(0, 0, length, 0);
            g2.drawLine(SpriteAnim.this._border.getWidth(), 0, SpriteAnim.this._border.getWidth() - length, 0);
            g2.drawLine(0, SpriteAnim.this._border.getHeight(), length, SpriteAnim.this._border.getHeight());
            g2.drawLine(SpriteAnim.this._border.getWidth(), SpriteAnim.this._border.getHeight(), SpriteAnim.this._border.getWidth() - length, SpriteAnim.this._border.getHeight());
            g2.drawLine(0, 0, 0, height);
            g2.drawLine(0, SpriteAnim.this._border.getHeight(), 0, SpriteAnim.this._border.getHeight() - height);
            g2.drawLine(SpriteAnim.this._border.getWidth(), 0, SpriteAnim.this._border.getWidth(), height);
            g2.drawLine(SpriteAnim.this._border.getWidth(), SpriteAnim.this._border.getHeight(), SpriteAnim.this._border.getWidth(), SpriteAnim.this._border.getHeight() - height);
        }
    };
    private Zone _selectZone;
    private SpriteObj _chooseMaps;
    private String _jogressMatch = "";
    private Integer[] _bosses;
    private SpriteObj _firstBoss;
    private SpriteObj _secondBoss;
    private SpriteObj _thirdBoss;
    private EvolutionInfo _boss1;
    private EvolutionInfo _boss2;
    private EvolutionInfo _boss3;
    private SpriteObj _digicore;
    private Clip _longClip;
    private SpriteObj _victoryMessage;
    private final Point MAP_SIZE = new Point(72, 48);
    private final Point MAP_LOC = new Point(52 - this._xPad, 59 - this._yPad);
    private boolean _started;
    private boolean _up;
    private boolean _success;

    public BackgroundAnim getBackgroundAnim() {
        return this._backgroundAnim;
    }

    public void setBackgroundAnim(BackgroundAnim a) {
        this._backgroundAnim = a;
    }

    public String getModFolder() {
        return this.MOD_FOLDER;
    }

    public String getResourcesFolder() {
        return this.RESOURCES_FOLDER;
    }

    public int getConsumablePage() {
        return this._consumablePage;
    }

    public void setConsumablePage(int i) {
        this._consumablePage = i;
    }

    public boolean setConsumablePage(boolean isShop, boolean isEvol, int page, Class<?> consumableType) {
        int max = this.getMaxConsumablePage(isShop, isEvol, consumableType);
        this._consumablePage = page > max ? 0 : (page < 0 ? max : page);
        return max > 0;
    }

    public boolean setConsumablePage(int size, int page) {
        int max = (int)Math.ceil((double)size / 4.0) - 1;
        this._consumablePage = page > max ? 0 : (page < 0 ? max : page);
        return max > 0;
    }

    public boolean setConsumablePage(Enum.Menu m, int page) {
        int max = this.getMaxConsumablePage(m);
        this._consumablePage = page > max ? 0 : (page < 0 ? max : page);
        return max > 0;
    }

    public int setShellPage(int page) {
        this._consumablePage = page > this._controller.getShells().size() - 1 ? 0 : (page < 0 ? this._controller.getShells().size() - 1 : page);
        this.drawCurrentShellToSettingsMenu();
        return this._consumablePage;
    }

    public void setDNAPage(int page) {
        this._consumablePage = page >= Enum.Field.values().length - 1 ? 0 : (page < 0 ? Enum.Field.values().length - 2 : page);
    }

    public void setHabitatCompatibilityPage(int page, Enum.Menu m) {
        Habitat habitat = this._controller.getModel().getDigimon().getHabitats().get(this._habitat);
        boolean c = m == Enum.Menu.Habitat_Compatibility || m == Enum.Menu.Habitat_Shop_Compatibility;
        int size = c ? habitat.getCompatibleElements().size() + habitat.getCompatibleFields().size() - 1 : habitat.getIncompatibleElements().size() + habitat.getIncompatibleFields().size() - 1;
        this._consumablePage = page > size ? 0 : (page < 0 ? size : page);
        this.drawHabitatCompatibility(m);
    }

    public MapLevel setMapPage(int page, boolean home) {
        MapLevel[] m = this._controller.getModel().getDigimon().getWorld().getTravelMaps();
        ArrayList<MapLevel> maps = new ArrayList<MapLevel>();
        if (home) {
            maps.add(this._controller.getModel().getDigimon().getWorld().getMaps().get(0));
        }
        maps.addAll(Arrays.asList(m));
        int length = maps.size() - (home ? 1 : 0);
        this._consumablePage = page > length ? 0 : (page < 0 ? length : page);
        MapLevel map = (MapLevel)maps.get(this._consumablePage);
        this.checkMap(map);
        return map;
    }

    public void setLevelPage(int page) {
        ArrayList<Integer> levels = this._controller.getModel().getDigimon().getUniqueLevelFought();
        int max = (int)Math.ceil((double)levels.size() / 3.0);
        this._consumablePage = page > max - 1 ? 0 : (page < 0 ? (max - 1 >= 0 ? max - 1 : 0) : page);
        this.drawLevelList(levels);
    }

    public int getHabitat() {
        return this._habitat;
    }

    public void resetHabitatPage() {
        this._habitat = -1;
    }

    public void setHabitat(int habitat, boolean isShop, boolean isDec) {
        ArrayList<Habitat> habitats;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        ArrayList<Habitat> arrayList = habitats = isShop ? digimon.getShopHabitats() : digimon.getOwnedHabitats();
        if (habitat < 0) {
            habitat = digimon.getHabitats().size() - 1;
        } else if (habitat >= digimon.getHabitats().size()) {
            habitat = 0;
        }
        while (!habitats.contains(digimon.getHabitats().get(habitat))) {
            if ((habitat += isDec ? -1 : 1) < 0) {
                habitat = digimon.getHabitats().size() - 1;
                continue;
            }
            if (habitat < digimon.getHabitats().size()) continue;
            habitat = 0;
        }
        if (habitat >= 0 && habitat < digimon.getHabitats().size()) {
            this._habitat = habitat;
        }
    }

    public boolean setEggPage(int page, Enum.Menu menu) {
        ArrayList<EvolutionInfo> e;
        switch (menu) {
            case Choose_Egg: {
                e = this._controller.getModel().getDigimon().getEvolution().getRestartDigimon();
                break;
            }
            default: {
                e = this._controller.getModel().getDigimon().getEvolution().getStartingDigimon();
            }
        }
        int max = e.size() - 1;
        this._consumablePage = page > max ? 0 : (page < 0 ? max : page);
        this.checkEggLabel(e);
        return max > 0;
    }

    public void setTrophyPage(int newPage, Enum.Season s) {
        this._trophyPage = newPage;
        int size = 0;
        switch (s) {
            case Spring: {
                size = (int)Math.ceil((double)this._controller.getModel().getDigimon().getTournament().getSpringTrophies().size() / (double)ViewConfig._trophyRecordsPageSize) - 1;
                if (this._trophyPage > size) {
                    this._trophyPage = 0;
                    break;
                }
                if (this._trophyPage >= 0) break;
                this._trophyPage = size;
                break;
            }
            case Summer: {
                size = (int)Math.ceil((double)this._controller.getModel().getDigimon().getTournament().getSummerTrophies().size() / (double)ViewConfig._trophyRecordsPageSize) - 1;
                if (this._trophyPage > size) {
                    this._trophyPage = 0;
                    break;
                }
                if (this._trophyPage >= 0) break;
                this._trophyPage = size;
                break;
            }
            case Fall: {
                size = (int)Math.ceil((double)this._controller.getModel().getDigimon().getTournament().getFallTrophies().size() / (double)ViewConfig._trophyRecordsPageSize) - 1;
                if (this._trophyPage > size) {
                    this._trophyPage = 0;
                    break;
                }
                if (this._trophyPage >= 0) break;
                this._trophyPage = size;
                break;
            }
            case Winter: {
                size = (int)Math.ceil((double)this._controller.getModel().getDigimon().getTournament().getWinterTrophies().size() / (double)ViewConfig._trophyRecordsPageSize) - 1;
                if (this._trophyPage > size) {
                    this._trophyPage = 0;
                    break;
                }
                if (this._trophyPage >= 0) break;
                this._trophyPage = size;
            }
        }
    }

    public int getTrophyPage() {
        return this._trophyPage;
    }

    public void setTrophyInSchedule(int t) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        int max = digimon.getTrophySchedule().length - 1;
        if (t > max) {
            t = 0;
        } else if (t < 0) {
            t = max;
        }
        this._trophyInSchedule = t;
        this.refreshTrophySchedule();
    }

    public int getTrophyInSchedule() {
        return this._trophyInSchedule;
    }

    public DisplayPane getMainInteract() {
        return this._mainInteract;
    }

    public DisplayPane getShell() {
        return this._shell;
    }

    public Weather getWeather() {
        return this._weather;
    }

    public ClockTic getController() {
        return this._controller;
    }

    public void setIsLoaded(boolean newLoad) {
        this._isLoaded = newLoad;
    }

    public boolean getIsLoaded() {
        return this._isLoaded;
    }

    public int getPosX() {
        return this._posx;
    }

    public void setPosX(int newX) {
        this._posx = newX;
    }

    public int getPosY() {
        return this._posy;
    }

    public void setPosY(int newY) {
        this._posy = newY;
    }

    public SpriteObj getCharacter() {
        return this._character;
    }

    private byte getScale() {
        return (byte)this._controller.getModel().getSettings().getGameScale();
    }

    public SpriteObj getEggLabel() {
        return this._eggLabel;
    }

    public JLabel getMinutesPane() {
        return this._minutesPane;
    }

    public JTextField getStringPane() {
        return this._stringPane;
    }

    public int getFrame() {
        return this._frame;
    }

    public void setFrame(int newFrame) {
        this._frame = this._interval * newFrame;
    }

    public boolean getUp() {
        return this._up;
    }

    public SpriteObj getTrainBarFull() {
        return this._trainBarFull;
    }

    public Enum.State getCurrentAnim() {
        return this._currentAnim;
    }

    public void setCurrentAnim(Enum.State newAnim) {
        this._currentAnim = newAnim;
    }

    public String getMessage() {
        return this._message;
    }

    public void setMessage(String message) {
        this._frame = -7 * this._interval;
        this._message = ViewUtil.getCenteredText(message);
    }

    public void setSuccess(boolean newSuccess) {
        this._success = newSuccess;
    }

    public boolean getSuccess() {
        return this._success;
    }

    public void setKeyboard(KeyboardCursor k) {
        this._keyboard = k;
    }

    public void setJogressMatch(String newMatch) {
        this._jogressMatch = newMatch;
    }

    public String getJogressMatch() {
        return this._jogressMatch;
    }

    public Zone getSelectZone() {
        return this._selectZone;
    }

    public SpriteObj getBattleFlash() {
        return this._battleFlash;
    }

    public void setTempDrag(boolean b) {
        this._tempDrag = b;
    }

    public SpriteObj getEvolutionTreeButton() {
        return this._evolutionTreeButton;
    }

    public SpriteObj getFoodLabel() {
        return this._foodLabel;
    }

    public SpriteObj getItemLabel() {
        return this._itemLabel;
    }

    public Item getItemType() {
        return this._itemType;
    }

    public void setItemType(Item i) {
        this._itemType = i;
    }

    public FoodType getFoodType() {
        return this._foodType;
    }

    public void setFoodType(FoodType f) {
        this._foodType = f;
    }

    public ShopConsumable getConsumableType() {
        return this._consumableType;
    }

    public SpriteAnim(SoundObj sounds, String modFolder, String resourceFolder) {
        this.setTitle("DVPet");
        this.MOD_FOLDER = modFolder + "images" + File.separator;
        this.RESOURCES_FOLDER = resourceFolder;
        this._sounds = sounds;
        this.setUndecorated(true);
        ViewUtil.setBackgroundColor(this, ViewConfig._transparentMenus ? 0.0f : 1.0f);
        this.setDefaultCloseOperation(3);
        this.getContentPane().setLayout(null);
        this.setIconImage(ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "PrgmIcon.png").getImage());
        this.setLocationRelativeTo(null);
        this.setVisible(true);
    }

    public void restartView(int scale, int shell, boolean isSound, boolean isOnTop) {
        this._controller.getModel().getSettings().setGameScale(scale);
        this._controller.getModel().getSettings().setShell(shell);
        this._controller.getModel().getSettings().setSound(isSound);
        this._controller.getModel().getSettings().setOnTop(isOnTop);
        this.setAlwaysOnTop(isOnTop);
        this._back.removeAll();
        this._shell.removeAll();
        this.setUndecorated(true);
        this.setDefaultCloseOperation(3);
        this.getContentPane().setLayout(null);
        this.setIconImage(ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "PrgmIcon.png").getImage());
        this.setLocationRelativeTo(null);
        this._backgroundAnim.resetDisplayedHabitat();
        this._frame = this._interval * -1;
        this._currentAnim = this._controller.getModel().getDigimon().getCurrentState();
        this.setupZones();
    }

    private void initComponents(PhysicalState digimon) {
        this._shell.setVisible(false);
        this._mainInteract.add(this._border);
        this._weather = new Weather(this.getScale(), 105, 69, this._sounds, this.MOD_FOLDER, this.RESOURCES_FOLDER);
        this._weather.startWeather(this._currentWeather);
        Icon i = ViewUtil.resizeImage(ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "userInput.png"), (double)this.getScale());
        this.initFont();
        this.initAttackButtons();
        this.initEggClockMenu();
        this.initSaveMenu();
        this.initMainMenu(digimon);
        this.initStartMenu();
        this.initSettingsMenu();
        this.initSaveLoadMenu(i);
        this.initStatusMenu();
        this.initFeedMenu();
        this.initPraiseMenu();
        this.initExerciseMenu();
        this.initBattleMenu(i);
        this.initMapMenu();
        this._menuRect = new Polygon(105 * this.getScale(), 60 * this.getScale(), ViewConfig._menuHighlightHex, ViewConfig._menuHighlightAlpha);
        this._menuRect.setVisible(false);
        this._mainDisplay.add(this._menuRect);
        this._mainDisplay.setSize(104 * this.getScale(), 60 * this.getScale());
        this._menuInteract.setVisible(false);
        this.add(this._interact);
        this._interact.add(this._menuInteract);
        this._interact.add(this._mainInteract);
        this.add(this._shell);
        this.add(this._overlay);
        this.add(this._display);
        this._display.add(this._mainDisplay);
        this.add(this._back);
    }

    private void initFont() {
        Font ttfBase = null;
        this._bit = null;
        try (InputStream stream = Utility.getInputStream(this.MOD_FOLDER, this.RESOURCES_FOLDER, "font.ttf");){
            ttfBase = Font.createFont(0, stream);
            this._bit = ttfBase.deriveFont(0, ViewConfig._fontSize * this.getScale());
            GraphicsEnvironment.getLocalGraphicsEnvironment().registerFont(this._bit);
        }
        catch (Exception ex) {
            ex.printStackTrace();
        }
    }

    private void checkArrows(KeyEvent key) {
        if (key.getKeyCode() == 44) {
            this._controller.onLeftComma();
        } else if (key.getKeyCode() == 46) {
            this._controller.onRightPeriod();
        }
    }

    private void initDebugMenu() {
        this._debugFrame = new JFrame();
        this._debugFrame.addKeyListener(new KeyAdapter(){

            @Override
            public void keyPressed(KeyEvent e) {
                SpriteAnim.this.checkArrows(e);
            }
        });
        this._debugFrame.setUndecorated(true);
        this._debugFrame.setDefaultCloseOperation(3);
        this._debugFrame.setLocation(this.getPosX() + this.getWidth(), this.getPosY());
        this._debugFrame.getContentPane().setLayout(null);
        this._debugFrame.setLocationRelativeTo(null);
        this._debugFrame.setVisible(true);
        this._debugFrame.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._posx = e.getX();
                SpriteAnim.this._posy = e.getY();
                SpriteAnim.this._debugFrame.requestFocus();
            }
        });
        this._debugFrame.addMouseMotionListener(new MouseAdapter(){

            @Override
            public void mouseDragged(MouseEvent evt) {
                SpriteAnim.this._debugFrame.setLocation(evt.getXOnScreen() - SpriteAnim.this._posx, evt.getYOnScreen() - SpriteAnim.this._posy);
            }
        });
        int rows = 50;
        int columns = 1;
        int height = 15;
        int width = 200;
        int x = 25;
        int y = 25;
        this._debugText1 = new JTextArea(rows, columns);
        Border border = BorderFactory.createLineBorder(Color.BLACK);
        this._debugText1.setBorder(BorderFactory.createCompoundBorder(border, BorderFactory.createEmptyBorder(10, 10, 10, 10)));
        this._debugText1.setBounds(x, y, width, rows * height);
        this._debugText1.setVisible(true);
        this._debugText1.setEditable(false);
        this._debugText2 = new JTextArea(rows, columns);
        this._debugText2.setBorder(BorderFactory.createCompoundBorder(border, BorderFactory.createEmptyBorder(10, 10, 10, 10)));
        this._debugText2.setBounds(width + x, y, width, rows * height);
        this._debugText2.setVisible(true);
        this._debugText2.setEditable(false);
        this._debugFrame.setSize(width * 2 + 50, rows * height + 50);
        this._debugFrame.getContentPane().add(this._debugText1);
        this._debugFrame.getContentPane().add(this._debugText2);
    }

    private void initSettingsMenu() {
        this._settingsMenu = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "settingsMenu.png", this._back, 175, 158, this.getScale());
        this._settingsMenu.setLocX(0);
        this._settingsMenu.setLocY(0);
        this._soundLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "sound.png", this._interact, 19, 17, this.getScale());
        this._soundLabel.setLocX(145);
        this._soundLabel.setLocY(68);
        this._soundLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "soundOff.png");
        this._soundLabel.addAltSprite(ViewUtil.getTransparentImage(this._soundLabel.getAltSprite("soundOff"), 0.25f), "soundOffTransp");
        this._soundLabel.addAltSprite(ViewUtil.getTransparentImage(this._soundLabel.getAltSprite("sound"), 0.25f), "soundTransp");
        this._soundLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                if (SpriteAnim.this._controller.getModel().getSettings().isSound()) {
                    SpriteAnim.this._soundLabel.setAltIcon("soundOff");
                } else {
                    SpriteAnim.this._soundLabel.setAltIcon("sound");
                }
                SpriteAnim.this._controller.onSound();
                if (SpriteAnim.this._controller.getModel().getSettings().isSound()) {
                    if (SpriteAnim.this._currentWeather == Enum.Weather.Raining || SpriteAnim.this._currentWeather == Enum.Weather.Drizzling || SpriteAnim.this._currentWeather == Enum.Weather.HeavyRain || SpriteAnim.this._currentWeather == Enum.Weather.Snowing || SpriteAnim.this._currentWeather == Enum.Weather.LightSnow || SpriteAnim.this._currentWeather == Enum.Weather.HeavySnow) {
                        SpriteAnim.this._weather.startWeather(SpriteAnim.this._currentWeather);
                    }
                } else if (SpriteAnim.this._currentWeather == Enum.Weather.Raining || SpriteAnim.this._currentWeather == Enum.Weather.Drizzling || SpriteAnim.this._currentWeather == Enum.Weather.HeavyRain || SpriteAnim.this._currentWeather == Enum.Weather.Snowing || SpriteAnim.this._currentWeather == Enum.Weather.LightSnow || SpriteAnim.this._currentWeather == Enum.Weather.HeavySnow) {
                    SpriteAnim.this._weather.stopWeather();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                if (SpriteAnim.this._controller.getModel().getSettings().isSound()) {
                    SpriteAnim.this._soundLabel.setAltIcon("sound");
                } else {
                    SpriteAnim.this._soundLabel.setAltIcon("soundOff");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this.checkSound();
            }
        });
        this._focusLabel = new SpriteObj("", "", "", this._interact, 16, 18, this.getScale());
        this._focusLabel.setLocX(146);
        this._focusLabel.setLocY(96);
        this._focusLabel.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "callLabel.png", (double)this.getScale() * 2.0), "callLabel");
        this._focusLabel.addAltSprite(ViewUtil.getTransparentImage(this._focusLabel.getAltSprite("callLabel"), 0.25f), "tCallLabel");
        this._focusLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                if (SpriteAnim.this._controller.getModel().getSettings().isFocus()) {
                    SpriteAnim.this._focusLabel.setAltIcon("callLabel");
                } else {
                    SpriteAnim.this._focusLabel.setAltIcon("tCallLabel");
                }
                SpriteAnim.this._controller.onFocusCall();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                if (!SpriteAnim.this._controller.getModel().getSettings().isFocus()) {
                    SpriteAnim.this._focusLabel.setAltIcon("callLabel");
                } else {
                    SpriteAnim.this._focusLabel.setAltIcon("tCallLabel");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getModel().getSettings().isFocus()) {
                    SpriteAnim.this._focusLabel.setAltIcon("callLabel");
                } else {
                    SpriteAnim.this._focusLabel.setAltIcon("tCallLabel");
                }
            }
        });
        this._onTopLabel = new SpriteObj("", "", "", this._interact, 17, 13, this.getScale());
        this._onTopLabel.setLocX(146);
        this._onTopLabel.setLocY(126);
        this._onTopLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "onTopLabel.png");
        this._onTopLabel.addAltSprite(ViewUtil.getTransparentImage(this._onTopLabel.getAltSprite("onTopLabel"), 0.25f), "tOnTopLabel");
        this._onTopLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                if (SpriteAnim.this._controller.getModel().getSettings().isOnTop()) {
                    SpriteAnim.this._onTopLabel.setAltIcon("onTopLabel");
                } else {
                    SpriteAnim.this._onTopLabel.setAltIcon("tOnTopLabel");
                }
                SpriteAnim.this._controller.onOnTop();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                if (!SpriteAnim.this._controller.getModel().getSettings().isOnTop()) {
                    SpriteAnim.this._onTopLabel.setAltIcon("onTopLabel");
                } else {
                    SpriteAnim.this._onTopLabel.setAltIcon("tOnTopLabel");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getModel().getSettings().isOnTop()) {
                    SpriteAnim.this._onTopLabel.setAltIcon("onTopLabel");
                } else {
                    SpriteAnim.this._onTopLabel.setAltIcon("tOnTopLabel");
                }
            }
        });
        this._smallScale = new SpriteObj("", "", "", this._interact, 7, 6, this.getScale());
        this._smallScale.setLocX(147);
        this._smallScale.setLocY(26);
        this._smallScale.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "smallSelect.png");
        this._smallScale.addAltSprite(ViewUtil.getTransparentImage(this._smallScale.getAltSprite("smallSelect"), 0.25f), "tSmallSelect");
        this._smallScale.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onScale((byte)1);
                SpriteAnim.this._smallScale.setAltIcon("smallSelect");
                SpriteAnim.this._mediumScale.setAltIcon("tMediumSelect");
                SpriteAnim.this._largeScale.setAltIcon("tLargeSelect");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._smallScale.setAltIcon("smallSelect");
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this.checkSettings();
            }
        });
        this._mediumScale = new SpriteObj("", "", "", this._interact, 11, 9, this.getScale());
        this._mediumScale.setLocX(147);
        this._mediumScale.setLocY(34);
        this._mediumScale.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "mediumSelect.png");
        this._mediumScale.addAltSprite(ViewUtil.getTransparentImage(this._mediumScale.getAltSprite("mediumSelect"), 0.25f), "tMediumSelect");
        this._mediumScale.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onScale((byte)2);
                SpriteAnim.this._mediumScale.setAltIcon("mediumSelect");
                SpriteAnim.this._smallScale.setAltIcon("tSmallSelect");
                SpriteAnim.this._largeScale.setAltIcon("tLargeSelect");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._mediumScale.setAltIcon("mediumSelect");
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this.checkSettings();
            }
        });
        this._largeScale = new SpriteObj("", "", "", this._interact, 15, 11, this.getScale());
        this._largeScale.setLocX(147);
        this._largeScale.setLocY(45);
        this._largeScale.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "largeSelect.png");
        this._largeScale.addAltSprite(ViewUtil.getTransparentImage(this._largeScale.getAltSprite("largeSelect"), 0.25f), "tLargeSelect");
        this._largeScale.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onScale((byte)3);
                SpriteAnim.this._largeScale.setAltIcon("largeSelect");
                SpriteAnim.this._smallScale.setAltIcon("tSmallSelect");
                SpriteAnim.this._mediumScale.setAltIcon("tMediumSelect");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._largeScale.setAltIcon("largeSelect");
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this.checkSettings();
            }
        });
    }

    private void checkKonami(KeyEvent key) {
        for (int i = 0; i < this._strokes.length; ++i) {
            if (this._strokes[i] != 0) continue;
            if (key.getKeyCode() == this.CODE[i]) {
                this._strokes[i] = key.getKeyCode();
                if (i != this._strokes.length - 1) break;
                this.codeMatch();
                break;
            }
            this._strokes = new int[9];
            break;
        }
    }

    private void codeMatch() {
        this._strokes = new int[9];
        if (this._debugFrame == null) {
            this.initDebugMenu();
        } else {
            this._debugFrame.setVisible(false);
            this._debugFrame = null;
            this._debugText1 = null;
            this._debugText2 = null;
        }
    }

    private boolean canChangeFastClock() {
        return (!this._controller.getModel().getDigimon().getTimeSkip() || Config._canTimeSkipAndChangeClockSpeed) && Config._canChangeClockSpeed && (Config._enableFastForward && this._currentAnim != Enum.State.Dying && this._currentAnim != Enum.State.BossParade || !Config._enableFastForward);
    }

    private void initStartMenu() {
        this.addKeyListener(new KeyAdapter(){

            @Override
            public void keyPressed(KeyEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getIsTournamentVersion() && SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Start) {
                    SpriteAnim.this.checkKonami(e);
                } else {
                    int key = e.getKeyCode();
                    if (SpriteAnim.this.canChangeFastClock() && key == ViewConfig._firstClockSpeedKey) {
                        SpriteAnim.this._controller.onFastClock(1);
                        SpriteAnim.this.setDynamicFastClockIcon(SpriteAnim.this._controller.getCurrentMenu(), 1);
                    } else if (SpriteAnim.this.canChangeFastClock() && key == ViewConfig._secondClockSpeedKey) {
                        SpriteAnim.this._controller.onFastClock(2);
                        SpriteAnim.this.setDynamicFastClockIcon(SpriteAnim.this._controller.getCurrentMenu(), 2);
                    } else if (SpriteAnim.this.canChangeFastClock() && key == ViewConfig._thirdClockSpeedKey) {
                        SpriteAnim.this._controller.onFastClock(3);
                        SpriteAnim.this.setDynamicFastClockIcon(SpriteAnim.this._controller.getCurrentMenu(), 3);
                    } else if (SpriteAnim.this.canChangeFastClock() && key == ViewConfig._fourthClockSpeedKey) {
                        SpriteAnim.this._controller.onFastClock(4);
                        SpriteAnim.this.setDynamicFastClockIcon(SpriteAnim.this._controller.getCurrentMenu(), 4);
                    } else if (key == ViewConfig._pauseKey && Utility.containsState(Utility.ENABLE_DURING_STATE, SpriteAnim.this._currentAnim)) {
                        SpriteAnim.this._controller.onPause();
                    } else if (key == ViewConfig._characterKey) {
                        SpriteAnim.this.characterButton();
                    } else if (key == ViewConfig._rightClickKey && SpriteAnim.this._menuButton.isVisible()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._frame = 0;
                        SpriteAnim.this._controller.reverseDataMenu();
                    }
                }
            }
        });
        MouseAdapter ma = new MouseAdapter(){
            boolean pressed = false;

            @Override
            public void mousePressed(MouseEvent event) {
                this.pressed = true;
                SpriteAnim.this._posx = event.getX();
                SpriteAnim.this._posy = event.getY();
            }

            @Override
            public void mouseReleased(MouseEvent event) {
                this.pressed = false;
            }

            @Override
            public void mouseDragged(MouseEvent event) {
                if (this.pressed) {
                    SpriteAnim.this.setLocation(event.getXOnScreen() - SpriteAnim.this._posx, event.getYOnScreen() - SpriteAnim.this._posy);
                }
            }
        };
        this.addMouseListener(ma);
        this.addMouseMotionListener(ma);
        this._closeButton = new SpriteObj("", "", "", this._interact, 13, 13, this.getScale());
        this._closeButton.setLocX(155);
        this._closeButton.setLocY(1);
        this._closeButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "highlightClose.png");
        this._closeButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onClose();
                SpriteAnim.this._closeButton.removeIcon();
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._closeButton.setAltIcon("highlightClose");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._closeButton.removeIcon();
            }
        });
        this._startMenu = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "startMenu.png", this._back, 165, 93, this.getScale());
        this._startMenu.setLocX(0);
        this._startMenu.setLocY(0);
        this._startButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "start.png", this._interact, this.getScale());
        this._startButton.setLocX(33);
        this._startButton.setLocY(67);
        this._startButton.addAltSprite(ViewUtil.getTransparentImage(this._startButton.getAltSprite("start"), 0.5f), "highlightStart");
        this._startButton.setAltIcon("highlightStart");
        this._startButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onNewGame();
                SpriteAnim.this._startButton.setAltIcon("highlightStart");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._startButton.setAltIcon("start");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._startButton.setAltIcon("highlightStart");
            }
        });
        this._loadButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "load.png", this._interact, this.getScale());
        this._loadButton.setLocX(88);
        this._loadButton.setLocY(67);
        this._loadButton.addAltSprite(ViewUtil.getTransparentImage(this._loadButton.getAltSprite("load"), 0.5f), "highlightLoad");
        this._loadButton.setAltIcon("highlightLoad");
        this._loadButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onLoadButton();
                SpriteAnim.this._loadButton.setAltIcon("highlightLoad");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._loadButton.setAltIcon("load");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._loadButton.setAltIcon("highlightLoad");
            }
        });
    }

    public synchronized void disposeMusic() {
        if (this._longClip != null) {
            new Thread(null, new Runnable(){

                @Override
                public void run() {
                    if (SpriteAnim.this._longClip != null) {
                        SpriteAnim.this._longClip.close();
                        SpriteAnim.this._longClip = null;
                    }
                }
            }, "DisposeMusic").start();
        }
    }

    private void initEggClockMenu() {
        this._newGameMenu = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "newGame.png", this._back, 210, 109, this.getScale());
        this._difficultyMenu = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "difficultyMenu.png", this._back, 229, 127, this.getScale());
        this._enterButton = new SpriteObj("", "", "", this._mainInteract, 17, 14, this.getScale());
        this._enterButton.setLocX(17);
        this._enterButton.setLocY(85);
        this._enterButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "highlightEnter.png");
        this._enterButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "enterButton.png");
        this._enterButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                if (SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Food_Purchase && SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Habitat_Purchase && SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Item_Purchase && (SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Tourney_Registration || SpriteAnim.this.canInteract())) {
                    if (SpriteAnim.this._controller.onEnter()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    }
                    SpriteAnim.this._enterButton.setAltIcon("enterButton");
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Food_Purchase && digimon.canBuy(SpriteAnim.this._consumableType.getPurchasePrice()) || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Item_Purchase && digimon.canBuy(SpriteAnim.this._consumableType.getPurchasePrice()) || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Habitat_Purchase && digimon.canBuy(digimon.getHabitats().get(SpriteAnim.this._habitat).getPrice())) {
                    if (SpriteAnim.this._controller.onEnter()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    }
                    SpriteAnim.this._enterButton.setAltIcon("enterButton");
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._enterButton.setAltIcon("highlightEnter");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._enterButton.setAltIcon("enterButton");
            }
        });
        this._fastClockDisplay = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fastClock.png", this._mainDisplay, 7, 14, this.getScale());
        this._fastClockDisplay.setLocX(78);
        this._fastClockDisplay.setLocY(54);
        this._fastClockDisplay.setHorizontalAlignment(2);
        this._fastClockDisplay.addAltSprite(ViewUtil.getTransparentImage(this._fastClockDisplay.getAltSprite("fastClock"), 0.25f), "tFastClock");
        this._fastClockDisplay.setAltIcon("tFastClock");
        this._timeSkipButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "timeSkip.png", this._mainInteract, 14, 15, this.getScale());
        this._timeSkipButton.setLocX(this._timeSkipButton.getSizeX() / this.getScale() / 2 + this._fastClockDisplay.getLocX() / this.getScale());
        this._timeSkipButton.setLocY(this._fastClockDisplay.getSizeY() / this.getScale() + this._fastClockDisplay.getLocY() / this.getScale());
        this._timeSkipButton.addAltSprite(ViewUtil.getTransparentImage(this._timeSkipButton.getAltSprite("timeSkip"), 0.25f), "tTimeSkip");
        this._timeSkipButton.addMouseListener(new MouseAdapter(){
            PhysicalState digimon;
            {
                this.digimon = SpriteAnim.this._controller.getModel().getDigimon();
            }

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Set_EggClock || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation && Config._canChangeTimeSkip) {
                    this.digimon.setTimeSkip(!this.digimon.getTimeSkip());
                    SpriteAnim.this._timeSkipButton.setAltIcon(SpriteAnim.this._controller.getModel().getDigimon().getTimeSkip() ? "timeSkip" : "tTimeSkip");
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Set_EggClock || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation && Config._canChangeTimeSkip) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Set_EggClock || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation && Config._canChangeTimeSkip) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._timeSkipButton, 5, 5, 3, true);
                }
            }
        });
        this._fastClockButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._mainInteract, 28, 14, this.getScale());
        this._fastClockButton.setLocX(78);
        this._fastClockButton.setLocY(54);
        this._fastClockButton.addAltSprite(ViewUtil.getTransparentImage(ViewUtil.resizeImage(ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fastClockTransparent.png"), (double)this.getScale()), 0.2f), "fastClockTransparent");
        this._fastClockButton.setAltIcon(0);
        this._fastClockButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                int speed = 1;
                int x = e.getPoint().x / SpriteAnim.this.getScale();
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                if (!ViewConfig._enableSingleClickClockSpeed) {
                    if (x >= 1 && x <= 7) {
                        speed = 1;
                    } else if (x > 7 && x <= 14) {
                        speed = 2;
                    } else if (x > 14 && x <= 21) {
                        speed = 3;
                    } else if (x > 21 && x <= 28) {
                        speed = 4;
                    }
                } else {
                    speed = SpriteAnim.this._controller.getModel().getTime().getFastMod();
                    if (++speed > 4) {
                        speed = 1;
                    }
                    this.mouseExited(e);
                    SpriteAnim.this._fastClockDisplay.setAltIcon("fastClock");
                }
                SpriteAnim.this._fastClockDisplay.setVisible(true);
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Set_EggClock || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation) {
                    SpriteAnim.this._timeSkipButton.setVisible(speed == 1);
                }
                if (speed != 1) {
                    if (SpriteAnim.this._timeSkipButton != null) {
                        SpriteAnim.this._timeSkipButton.setAltIcon("tTimeSkip");
                    }
                    SpriteAnim.this._controller.getModel().getDigimon().setTimeSkip(false);
                    SpriteAnim.this._keyboard.getInteractiveButtons().remove(SpriteAnim.this._timeSkipButton);
                } else if (!SpriteAnim.this._keyboard.getInteractiveButtons().contains(SpriteAnim.this._timeSkipButton)) {
                    SpriteAnim.this._keyboard.addButton(SpriteAnim.this._timeSkipButton, 5);
                }
                SpriteAnim.this._controller.onFastClock(speed);
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._fastClockDisplay.setAltIcon("tFastClock");
                SpriteAnim.this.changeFastClockDisplayWidth(SpriteAnim.this._controller.getModel().getTime().getFastMod());
                SpriteAnim.this._fastClockDisplay.setVisible(true);
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._fastClockDisplay.setAltIcon("fastClock");
            }
        });
        this._fastClockButton.addMouseMotionListener(new MouseAdapter(){

            @Override
            public void mouseMoved(MouseEvent evt) {
                int x = evt.getPoint().x / SpriteAnim.this.getScale();
                if (x > 0 && x <= 7) {
                    int newSize = 7;
                    if (SpriteAnim.this._fastClockDisplay.getSizeX() != newSize * SpriteAnim.this.getScale()) {
                        // empty if block
                    }
                    SpriteAnim.this._fastClockDisplay.setSizeX(newSize);
                } else if (x > 7 && x <= 14) {
                    int newSize = 14;
                    if (SpriteAnim.this._fastClockDisplay.getSizeX() != newSize * SpriteAnim.this.getScale()) {
                        // empty if block
                    }
                    SpriteAnim.this._fastClockDisplay.setSizeX(newSize);
                } else if (x > 14 && x <= 21) {
                    int newSize = 21;
                    if (SpriteAnim.this._fastClockDisplay.getSizeX() != newSize * SpriteAnim.this.getScale()) {
                        // empty if block
                    }
                    SpriteAnim.this._fastClockDisplay.setSizeX(newSize);
                } else if (x > 21 && x <= 28) {
                    int newSize = 28;
                    if (SpriteAnim.this._fastClockDisplay.getSizeX() != newSize * SpriteAnim.this.getScale()) {
                        // empty if block
                    }
                    SpriteAnim.this._fastClockDisplay.setSizeX(newSize);
                }
                SpriteAnim.this._fastClockDisplay.setVisible(true);
            }
        });
        this._rightButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "arrow.png", this._mainInteract, 12, 24, this.getScale());
        this._rightButton.setLocX(182);
        this._rightButton.setLocY(39);
        this._rightButton.getAltSprite("arrow").setDescription("right");
        this._rightButton.addAltSprite(ViewUtil.resizeImage(this._rightButton.getAltSprite("right"), 0.5), "small");
        this._rightButton.addAltSprite(ViewUtil.getTransparentImage(this._rightButton.getAltSprite("right"), 0.25f), "highlightRight");
        this._rightButton.addAltSprite(ViewUtil.getTransparentImage(this._rightButton.getAltSprite("small"), 0.25f), "tSmall");
        this._rightButton.setAltIcon("highlightRight");
        this._rightButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.onCycleRight()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                if (!SpriteAnim.this._rightButton.getCurrentAltIcon().equals("small") && !SpriteAnim.this._rightButton.getCurrentAltIcon().equals("tSmall")) {
                    SpriteAnim.this._rightButton.setAltIcon("right");
                } else {
                    SpriteAnim.this._rightButton.setAltIcon("small");
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (!SpriteAnim.this._rightButton.getCurrentAltIcon().equals("small") && !SpriteAnim.this._rightButton.getCurrentAltIcon().equals("tSmall")) {
                    SpriteAnim.this._rightButton.setAltIcon("highlightRight");
                } else {
                    SpriteAnim.this._rightButton.setAltIcon("tSmall");
                }
            }
        });
        this._leftButton = new SpriteObj("", "", "", this._mainInteract, 12, 24, this.getScale());
        this._leftButton.setLocX(120);
        this._leftButton.setLocY(39);
        this._leftButton.addAltSprite(ViewUtil.flipHorizontally(this._rightButton.getAltSprite("right")), "left");
        this._leftButton.addAltSprite(ViewUtil.getTransparentImage(this._leftButton.getAltSprite("left"), 0.25f), "highlightLeft");
        this._leftButton.addAltSprite(ViewUtil.resizeImage(this._leftButton.getAltSprite("left"), 0.5), "small");
        this._leftButton.addAltSprite(ViewUtil.getTransparentImage(this._leftButton.getAltSprite("small"), 0.25f), "tSmall");
        this._leftButton.setAltIcon("highlightLeft");
        this._leftButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.onCycleLeft()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                if (!SpriteAnim.this._leftButton.getCurrentAltIcon().equals("small") && !SpriteAnim.this._leftButton.getCurrentAltIcon().equals("tSmall")) {
                    SpriteAnim.this._leftButton.setAltIcon("left");
                } else {
                    SpriteAnim.this._leftButton.setAltIcon("small");
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (!SpriteAnim.this._leftButton.getCurrentAltIcon().equals("small") && !SpriteAnim.this._leftButton.getCurrentAltIcon().equals("tSmall")) {
                    SpriteAnim.this._leftButton.setAltIcon("highlightLeft");
                } else {
                    SpriteAnim.this._leftButton.setAltIcon("tSmall");
                }
            }
        });
        this._upButton = new SpriteObj("", "", "", this._display, 24, 12, this.getScale());
        this._upButton.setVisible(false);
        Icon up = ViewUtil.getRotatedIcon(3, this._rightButton.getAltSprite("right"));
        this._upButton.addAltSprite(up, "up");
        this._upButton.addAltSprite(ViewUtil.getTransparentImage(this._upButton.getAltSprite("up"), 0.25f), "tUp");
        this._upButton.setAltIcon("tUp");
        this._upButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onCycleUp();
                SpriteAnim.this._keyboard.setCursorPosition(-1);
                SpriteAnim.this._upButton.setAltIcon("tUp");
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._upButton.setAltIcon("up");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._upButton.setAltIcon("tUp");
            }
        });
        this._downButton = new SpriteObj("", "", "", this._display, 24, 12, this.getScale());
        this._downButton.setVisible(false);
        Icon down = ViewUtil.getRotatedIcon(1, this._rightButton.getAltSprite("right"));
        this._downButton.addAltSprite(down, "down");
        this._downButton.addAltSprite(ViewUtil.getTransparentImage(this._downButton.getAltSprite("down"), 0.25f), "tDown");
        this._downButton.setAltIcon("tDown");
        this._downButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._keyboard.setCursorPosition(-1);
                SpriteAnim.this._downButton.setAltIcon("tDown");
                SpriteAnim.this._controller.onCycleDown();
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._downButton.setAltIcon("down");
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                SpriteAnim.this._downButton.setAltIcon("tDown");
            }
        });
        this._eggLabel = new SpriteObj("", "", "", this._mainDisplay, 48, 48, this.getScale());
        this._eggLabel.setVisible(false);
        this._eggLabel.setLocX(133);
        this._eggLabel.setLocY(27);
        this._eggLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onDifficulty(2);
                } else if (SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Set_EggClock) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onChooseEgg();
                    SpriteAnim.this._eggLabel.setVisible(false);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._eggLabel, 5, 5, 3, true);
                } else if (SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Set_EggClock) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._eggLabel, 3, 2, 2, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.Set_EggClock) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        Font timeFont = this._bit.deriveFont((float)(48 * this.getScale()));
        this._shopHours = new SpriteObj("", "", "", this._mainDisplay, 88, 30, this.getScale());
        this._shopHours.setFont(this._bit.deriveFont((float)(24 * this.getScale())));
        this._shopHours.setForeground(Color.BLACK);
        this._hoursPane = new JLabel();
        this._hoursPane.setBounds(13 * this.getScale(), 40 * this.getScale(), 90 * this.getScale(), 48 * this.getScale());
        this._hoursPane.setText("00");
        this._hoursPane.setBorder(null);
        this._hoursPane.setFont(timeFont);
        this._hoursPane.setForeground(Color.BLACK);
        this._mainDisplay.add(this._hoursPane);
        this._minutesPane = new JLabel();
        this._minutesPane.setBounds(48 * this.getScale(), 40 * this.getScale(), 36 * this.getScale(), 48 * this.getScale());
        this._minutesPane.setText("00");
        this._minutesPane.setBorder(null);
        this._minutesPane.setFont(timeFont);
        this._minutesPane.setForeground(Color.BLACK);
        this._mainDisplay.add(this._minutesPane);
        this._colonLabel = new SpriteObj("", "", "", this._mainDisplay, 15, 20, this.getScale());
        this._colonLabel.setText(":");
        this._colonLabel.setFont(this._bit.deriveFont((float)(60 * this.getScale())));
        this._colonLabel.setForeground(Color.BLACK);
        this._colonLabel.setLocX(42);
        this._colonLabel.setLocY(51);
        this._timeLabel = new SpriteObj("", "", "", this._mainDisplay, 30, 30, this.getScale());
        this._timeLabel.setLoc(26 - this._xPad, 54 - this._yPad);
        this._timeLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "night.png");
        this._timeLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "noon.png");
        this._timeLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "morning.png");
        this._plusHoursButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "addButton.png", this._mainInteract, 20, 19, this.getScale());
        this._plusHoursButton.setLocX(16);
        this._plusHoursButton.setLocY(30);
        this._plusHoursButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "addPressed.png");
        Icon i = ViewUtil.getTransparentImage(this._plusHoursButton.getAltSprite("addButton"), 0.25f);
        this._plusHoursButton.addAltSprite(i, "tAddButton");
        this._plusHoursButton.setAltIcon("tAddButton");
        this._plusHoursButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._plusHoursButton.setAltIcon("addPressed");
                SpriteAnim.this._hoursPane.setText(SpriteAnim.this.changeHour(SpriteAnim.this._hoursPane.getText(), true));
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                SpriteAnim.this._plusHoursButton.setAltIcon("addButton");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._plusHoursButton.setAltIcon("addButton");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._plusHoursButton.setAltIcon("tAddButton");
            }
        });
        this._minusHoursButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "subtractButton.png", this._mainInteract, 20, 19, this.getScale());
        this._minusHoursButton.setLocX(16);
        this._minusHoursButton.setLocY(74);
        this._minusHoursButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "subtractPressed.png");
        i = ViewUtil.getTransparentImage(this._minusHoursButton.getAltSprite("subtractButton"), 0.25f);
        this._minusHoursButton.addAltSprite(i, "tSubtractButton");
        this._minusHoursButton.setAltIcon("tSubtractButton");
        this._minusHoursButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._minusHoursButton.setAltIcon("subtractPressed");
                SpriteAnim.this._hoursPane.setText(SpriteAnim.this.changeHour(SpriteAnim.this._hoursPane.getText(), false));
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                SpriteAnim.this._minusHoursButton.setAltIcon("subtractButton");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._minusHoursButton.setAltIcon("tSubtractButton");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._minusHoursButton.setAltIcon("subtractButton");
            }
        });
        this._plusMinutesButton = new SpriteObj("", "", "", this._mainInteract, 20, 19, this.getScale());
        this._plusMinutesButton.setLocX(51);
        this._plusMinutesButton.setLocY(30);
        this._plusMinutesButton.addAltSprite(this._plusHoursButton.getAltSprite("addButton"), "addButton");
        this._plusMinutesButton.addAltSprite(this._plusHoursButton.getAltSprite("addPressed"), "addPressed");
        this._plusMinutesButton.setAltIcon("addButton");
        this._plusMinutesButton.addAltSprite(this._plusHoursButton.getAltSprite("tAddButton"), "tAddButton");
        this._plusMinutesButton.setAltIcon("tAddButton");
        this._plusMinutesButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._plusMinutesButton.setAltIcon("addPressed");
                SpriteAnim.this._minutesPane.setText(SpriteAnim.this.changeMinute(SpriteAnim.this._minutesPane.getText(), true));
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                SpriteAnim.this._plusMinutesButton.setAltIcon("addButton");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._plusMinutesButton.setAltIcon("addButton");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._plusMinutesButton.setAltIcon("tAddButton");
            }
        });
        this._minusMinutesButton = new SpriteObj("", "", "", this._mainInteract, 20, 19, this.getScale());
        this._minusMinutesButton.setLocX(51);
        this._minusMinutesButton.setLocY(74);
        this._minusMinutesButton.addAltSprite(this._minusHoursButton.getAltSprite("subtractButton"), "subtractButton");
        this._minusMinutesButton.addAltSprite(this._minusHoursButton.getAltSprite("subtractPressed"), "subtractPressed");
        this._minusMinutesButton.setAltIcon("subtractButton");
        this._minusMinutesButton.addAltSprite(this._minusHoursButton.getAltSprite("tSubtractButton"), "tSubtractButton");
        this._minusMinutesButton.setAltIcon("tSubtractButton");
        this._minusMinutesButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._minusMinutesButton.setAltIcon("subtractPressed");
                SpriteAnim.this._minutesPane.setText(SpriteAnim.this.changeMinute(SpriteAnim.this._minutesPane.getText(), false));
            }

            @Override
            public void mouseReleased(MouseEvent evt) {
                SpriteAnim.this._minusMinutesButton.setAltIcon("subtractButton");
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._minusMinutesButton.setAltIcon("subtractButton");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._minusMinutesButton.setAltIcon("tSubtractButton");
            }
        });
    }

    public String getTimeFromPanel() {
        return this._hoursPane.getText() + ":" + this._minutesPane.getText();
    }

    private String changeHour(String s, boolean inc) {
        int hour = Integer.parseInt(s) + (inc ? 1 : -1);
        if (hour > 23) {
            hour = 0;
        } else if (hour < 0) {
            hour = 23;
        }
        return this.getExtraZero(Integer.toString(hour));
    }

    private String changeMinute(String s, boolean inc) {
        int min = Integer.parseInt(s) + (inc ? 1 : -1);
        if (min > 59) {
            min = 0;
        } else if (min < 0) {
            min = 59;
        }
        return this.getExtraZero(Integer.toString(min));
    }

    private String getExtraZero(String time) {
        String zero = time;
        if (time.length() == 1) {
            zero = "0" + time;
        }
        return zero;
    }

    private void initSaveLoadMenu(Icon icon) {
        Font f = this._bit.deriveFont((float)(28 * this.getScale()));
        this._userInputTitle = new JLabel();
        this._userInputTitle.setBounds(6 * this.getScale(), 18 * this.getScale(), 60 * this.getScale(), 19 * this.getScale());
        this._userInputTitle.setText("Save");
        this._userInputTitle.setBorder(null);
        this._userInputTitle.setFont(f);
        this._userInputTitle.setForeground(Color.BLACK);
        this._userInputTitle.setVisible(false);
        this._back.add(this._userInputTitle);
        this._saveLoadMenu = new SpriteObj("", "", "", this._back, 184, 67, this.getScale());
        this._saveLoadMenu.setIcon(icon);
        int length = 7;
        this.initStringPane(length);
    }

    private void initMainMenu(PhysicalState digimon) {
        this._rect = new Polygon(105 * this.getScale(), 60 * this.getScale(), 0, 0, 0, 0);
        this._overlay.add(this._rect);
        this._animRect = new Polygon(105 * this.getScale(), 60 * this.getScale(), 0, 0, 0, 0);
        this._overlay.add(this._animRect);
        this._animRect.setVisible(false);
        this._adventureBar = new Polygon(0, 3 * this.getScale(), 0, 0, 0, 255);
        this._mainDisplay.add(this._adventureBar);
        this._tempFill = new Polygon(93 * this.getScale(), 4 * this.getScale(), 0, 0, 0, 255);
        this._tempFillDefaultSize = this._tempFill.getWidth();
        this._mainDisplay.add(this._tempFill);
        this._tempFill.setLocation(5 * this.getScale(), 33 * this.getScale());
        this._washLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "wash.png", this._mainDisplay, 42, 63, this.getScale());
        this._washLabel.setLocX(-100);
        this._washLabel.setLocY(54 - this._yPad);
        this._select = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "select.png", this._mainDisplay, 6, 12, this.getScale());
        this._select.addAltSprite(ViewUtil.flipIcon(this._select.getAltSprite("select")), "selectMirror");
        this._roomEffect = new SpriteObj("", "", "", this._mainDisplay, 105, 60, this.getScale());
        this._roomEffect.setLocX(26 - this._xPad);
        this._roomEffect.setLocY(0);
        this._mainDisplay.add(this._weather.getOverlay());
        this._foodLabel = new SpriteObj("", "", "", this._mainDisplay, 24, 24, this.getScale());
        this._itemLabel = new SpriteObj("", "", "", this._mainDisplay, 48, 48, this.getScale());
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attackHit.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "shopClosed.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "connectionError.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "mismatch.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attackHitFlash.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evol.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "lightsOff.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "sleepLightsOff.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "sleepLightsOff2.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "loading.gif");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "world.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "dnaWash.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "dnaGenerateValidation.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "napLightsOff.png");
        this._roomEffect.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "napLightsOff2.png");
        this._digicore = new SpriteObj("", "", "", this._mainDisplay, 56, 56, this.getScale());
        this._digicore.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "xAntibodyNoReq.png", (double)this.getScale() * 1.5), "xAntibodyNoReq");
        this._digicore.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "xAntibodyReq.png", (double)this.getScale() * 1.5), "xAntibodyReq");
        this._digicore.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "xAntibodyTemp.png", (double)this.getScale() * 1.5), "xAntibodyTemp");
        this._digicore.addMouseListener(new MouseAdapter(){
            PhysicalState digimon;
            {
                this.digimon = SpriteAnim.this._controller.getModel().getDigimon();
            }

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.EvolutionState) {
                    if (this.digimon.getAlive()) {
                        ArrayList<EvolutionInfo> evolutions = this.digimon.getEvolution().getCurrentNaturalEvol(this.digimon);
                        if (evolutions != null && !evolutions.isEmpty()) {
                            SpriteAnim.this._sounds.playSound(SoundConfig._click);
                            SpriteAnim.this._currentAnim = null;
                            SpriteAnim.this._controller.onDigicore();
                        } else {
                            SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        }
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.EvolutionState) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._select.setLocX(SpriteAnim.this._digicore.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._digicore.getSizeX() / SpriteAnim.this.getScale());
                    SpriteAnim.this._select.setLocY(SpriteAnim.this._digicore.getLocY() / SpriteAnim.this.getScale() + 23);
                    SpriteAnim.this._select.setVisible(true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.EvolutionState) {
                    SpriteAnim.this._select.setLocX(-100);
                }
            }
        });
        this._filthLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._mainDisplay, 0, 60, this.getScale());
        this._filthLabel.setLocX(0);
        this._filthLabel.setLocY(0);
        this._character = new SpriteObj("", "", "", this._mainDisplay, 48, 48, this.getScale());
        this._character.setVisible(false);
        this.addCharacterListener(this._character, digimon);
        this._character.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "death.png");
        this._frozen = ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "frozen.png");
        this._frozen = ViewUtil.resizeImage(this._frozen, (double)this.getScale());
        this._opponent = new SpriteObj("", "", "", this._mainDisplay, 20, 58, this.getScale());
        this._opponent.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onDifficulty(1);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._opponent, 5, 5, 3, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        this._emotionLabel = new SpriteObj("", "", "", this._mainDisplay, 24, 24, this.getScale());
        this._emotionLabel.setLocX(103 - this._xPad);
        this._emotionLabel.setLocY(56 - this._yPad);
        this._emotionLabel.setFont(this._bit.deriveFont((float)(60 * this.getScale())));
        this._emotionLabel.setForeground(Color.BLACK);
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "happy.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "unhappy.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "unhappy2.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "napLights.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "napLights2.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "sleepLights.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "sleepLights2.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attention.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "dying.png");
        this._emotionLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "dying2.png");
        this._background = new SpriteObj("", "", "", this._back, 104, 101, this.getScale());
        this._backgroundAnim = new BackgroundAnim(this._background, this._rect, this.MOD_FOLDER, this.RESOURCES_FOLDER);
        this._mainBackground = new SpriteObj("", "", "", this._shell, 0, 0, this.getScale());
        this._statusButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._feedButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._digisoulButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._gameButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._battleButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._washButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._lightButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._firstAidButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._tempButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._callIcon = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._evolutionTreeButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._mapButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._clockButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._settingsButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._saveButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "", this._menuInteract, this.getScale());
        this._states = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "state.png", this._display, 7, 7, 2, this.getScale());
        this._states.setVisible(false);
        this._bandageState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._bandageState.setLocX(120 - this._xPad);
        this._bandageState.setLocY(83 - this._yPad);
        this._bandageState.setVisible(false);
        this._injuryState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._injuryState.setLocX(120 - this._xPad);
        this._injuryState.setLocY(73 - this._yPad);
        this._injuryState.setVisible(false);
        this._medicineState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._medicineState.setLocX(121 - this._xPad);
        this._medicineState.setLocY(64 - this._yPad);
        this._medicineState.setVisible(false);
        this._sickState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._sickState.setLocX(120 - this._xPad);
        this._sickState.setLocY(55 - this._yPad);
        this._sickState.setVisible(false);
        this._vitaminState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._vitaminState.setLocX(120 - this._xPad);
        this._vitaminState.setLocY(93 - this._yPad);
        this._vitaminState.setVisible(false);
        this._fatigueState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._fatigueState.setLocX(121 - this._xPad);
        this._fatigueState.setLocY(103 - this._yPad);
        this._fatigueState.setVisible(false);
        this._teachState = new SpriteObj("", "", "", this._mainDisplay, 7, 7, this.getScale());
        this._teachState.setVisible(false);
        this._restartLabel = new SpriteObj("", "", "", this._mainDisplay, 72, 18, this.getScale());
        this._restartLabel.setText("Restart");
        this._restartLabel.setFont(this._bit);
        this._restartLabel.setForeground(Color.BLACK);
        this._restartLabel.setLocX(47 - this._xPad);
        this._restartLabel.setLocY(59 - this._yPad);
        this._seasonLabel = new SpriteObj("", "", "", this._mainInteract, 22, 21, this.getScale());
        this._seasonLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "spring.png");
        this._seasonLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "summer.png");
        this._seasonLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fall.png");
        this._seasonLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "winter.png");
        this._tempLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "tempSmall.png", this._mainInteract, 10, 16, 1, this.getScale());
        this._prizeButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "prize.png", this._mainInteract, 13, 13, this.getScale());
        this._prizeButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "tPrize.png");
        this._prizeButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Tourney_Enter: {
                        SpriteAnim.this._controller.onPrize();
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Tourney_Enter: {
                        SpriteAnim.this._prizeButton.setAltIcon("prize");
                    }
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Tourney_Enter: {
                        SpriteAnim.this._prizeButton.setAltIcon("tPrize");
                    }
                }
            }
        });
        this._optionButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "option.png", this._mainInteract, 14, 14, this.getScale());
        this._optionButton.setVerticalAlignment(3);
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("option"), 0.25f), "tOption");
        this._optionButton.setAltIcon("tOption");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "modeChange.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("modeChange"), 0.25f), "tModeChange");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "nutrition.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("nutrition"), 0.25f), "tNutrition");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "calories.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("calories"), 0.25f), "tCalories");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleLevel.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("battleLevel"), 0.25f), "tBattleLevel");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "alarm.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("alarm"), 0.25f), "tAlarm");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "alarmSwitch.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("alarmSwitch"), 0.25f), "tAlarmSwitch");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "assistant.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("assistant"), 0.25f), "tAssistant");
        this._optionButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "favoriteMenu.png");
        this._optionButton.addAltSprite(ViewUtil.getTransparentImage(this._optionButton.getAltSprite("favoriteMenu"), 0.25f), "favoriteMenuTransp");
        this._optionButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Buy_Nutrition: 
                    case Use_Nutrition: 
                    case Med_Nutrition: 
                    case Sell_Nutrition: {
                        SpriteAnim.this._controller.onCalories();
                        break;
                    }
                    case Data_Nutrition: {
                        SpriteAnim.this._controller.onDigimonCalories();
                        break;
                    }
                    case Set_AutoCare: {
                        SpriteAnim.this.checkAutoCare(digimon.setAutoCare(!digimon.getAutoCare()));
                        break;
                    }
                    case PraiseScold_Validation: {
                        SpriteAnim.this._controller.onAutoCareValidation();
                        break;
                    }
                    case Data_Battles: {
                        SpriteAnim.this._controller.onBattleLevel();
                        break;
                    }
                    case Battle_Validation: {
                        SpriteAnim.this._controller.onBattleOptions();
                        break;
                    }
                    case Tourney_Enter: {
                        SpriteAnim.this._controller.onTourneyAlarm(SpriteAnim.this.getCurrentSelectedTrophy(digimon).getID());
                        SpriteAnim.this.checkTourneyAlarmSwitch(digimon);
                        break;
                    }
                    case EvolutionState: {
                        SpriteAnim.this._controller.onModeChange();
                        SpriteAnim.this._backgroundAnim.checkBackNoAnim(digimon, SpriteAnim.this._controller.getCurrentMenu(), SpriteAnim.this.getScale(), SpriteAnim.this._controller.getBattle());
                        break;
                    }
                    case Data_Hunger: 
                    case Buy_Food: 
                    case Use_Food: 
                    case Use_Med_Food: 
                    case Sell_Food: {
                        SpriteAnim.this._controller.onNutrition();
                        break;
                    }
                    case Data_Person: {
                        SpriteAnim.this._controller.onDataFavorites();
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Buy_Nutrition: 
                    case Use_Nutrition: 
                    case Med_Nutrition: 
                    case Sell_Nutrition: 
                    case Data_Nutrition: {
                        SpriteAnim.this._optionButton.setAltIcon("calories");
                        break;
                    }
                    case Set_AutoCare: {
                        SpriteAnim.this.setBorder(SpriteAnim.this._optionButton, 4, 4, 3, true);
                        break;
                    }
                    case PraiseScold_Validation: {
                        SpriteAnim.this._optionButton.setAltIcon("assistant");
                        break;
                    }
                    case Data_Battles: {
                        SpriteAnim.this._optionButton.setAltIcon("battleLevel");
                        break;
                    }
                    case Battle_Validation: {
                        SpriteAnim.this._optionButton.setAltIcon("option");
                        break;
                    }
                    case Tourney_Enter: {
                        SpriteAnim.this.setBorder(SpriteAnim.this._optionButton, 3, 3, 2, true);
                        break;
                    }
                    case EvolutionState: {
                        SpriteAnim.this._optionButton.setAltIcon("modeChange");
                        break;
                    }
                    case Data_Hunger: 
                    case Buy_Food: 
                    case Use_Food: 
                    case Use_Med_Food: 
                    case Sell_Food: {
                        SpriteAnim.this._optionButton.setAltIcon("nutrition");
                        break;
                    }
                    case Data_Person: {
                        SpriteAnim.this._optionButton.setAltIcon("favoriteMenu");
                    }
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Buy_Nutrition: 
                    case Use_Nutrition: 
                    case Med_Nutrition: 
                    case Sell_Nutrition: 
                    case Data_Nutrition: {
                        SpriteAnim.this._optionButton.setAltIcon("tCalories");
                        break;
                    }
                    case Set_AutoCare: {
                        SpriteAnim.this._border.setVisible(false);
                        break;
                    }
                    case PraiseScold_Validation: {
                        SpriteAnim.this._optionButton.setAltIcon("tAssistant");
                        break;
                    }
                    case Data_Battles: {
                        SpriteAnim.this._optionButton.setAltIcon("tBattleLevel");
                        break;
                    }
                    case Battle_Validation: {
                        SpriteAnim.this._optionButton.setAltIcon("tOption");
                        break;
                    }
                    case Tourney_Enter: {
                        SpriteAnim.this._border.setVisible(false);
                        break;
                    }
                    case EvolutionState: {
                        SpriteAnim.this._optionButton.setAltIcon("tModeChange");
                        break;
                    }
                    case Data_Hunger: 
                    case Buy_Food: 
                    case Use_Food: 
                    case Use_Med_Food: 
                    case Sell_Food: {
                        SpriteAnim.this._optionButton.setAltIcon("tNutrition");
                        break;
                    }
                    case Data_Person: {
                        SpriteAnim.this._optionButton.setAltIcon("favoriteMenuTransp");
                    }
                }
            }
        });
        this._personLabel = new SpriteObj("", "", "", this._mainInteract, 86, 21, this.getScale());
        this._personLabel.setBorder(null);
        this._personLabel.setFont(this._bit);
        this._personLabel.setForeground(Color.BLACK);
        this._personLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (Config._showPersonalityMenu && SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Person) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onPerson();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (Config._showPersonalityMenu && SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Person) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._select.setLocX(SpriteAnim.this._personLabel.getLocX() / SpriteAnim.this.getScale() + ((SpriteAnim)SpriteAnim.this)._personLabel.getPreferredSize().width / SpriteAnim.this.getScale() + 1);
                    SpriteAnim.this._select.setLocY(SpriteAnim.this._personLabel.getLocY() / SpriteAnim.this.getScale() + 1);
                    SpriteAnim.this._select.setVisible(true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (Config._showPersonalityMenu && SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Person) {
                    SpriteAnim.this._select.setLocX(-100);
                }
            }
        });
        this._menuButton = new SpriteObj("", "", "", this._mainInteract, 105, 69, this.getScale());
        this._menuButton.setLocX(27 - this._xPad);
        this._menuButton.setLocY(48 - this._yPad);
        this.addMainMenuListeners();
    }

    private void initStatusMenu() {
        String winRate = this._controller.getModel().getDigimon().getWinRate() + "%";
        this._winRatePanel = new JLabel();
        this._winRatePanel.setBorder(null);
        this._winRatePanel.setFont(this._bit);
        this._winRatePanel.setText(winRate);
        this._winRatePanel.setBounds((46 - this._xPad) * this.getScale(), (68 - this._yPad) * this.getScale(), 90 * this.getScale(), ViewConfig._fontSize * this.getScale());
        this._winRatePanel.setForeground(Color.BLACK);
        this._mainDisplay.add(this._winRatePanel);
        this._battlesPanel = new SpriteObj("", "", "", this._mainDisplay, 100, ViewConfig._fontSize, this.getScale());
        this._battlesPanel.setBorder(null);
        this._battlesPanel.setFont(this._bit);
        this._battlesPanel.setForeground(Color.BLACK);
        this._battlesPanel.setLoc(33 - this._xPad, 50 - this._yPad);
        this._bitsLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "bits.png", this._mainDisplay, (byte)(this.getScale() * 3));
        this._bitsLabel.setRawLoc(3 * this.getScale(), 37 * this.getScale());
        this._bitsPanel = new SpriteObj("", "", "", this._mainDisplay, 100, ViewConfig._fontSize, this.getScale());
        this._bitsPanel.setBorder(null);
        this._bitsPanel.setFont(this._bit);
        this._bitsPanel.setForeground(Color.BLACK);
        this._bitsPanel.setLocY(89 - this._yPad);
        this._bitsPanel.setLocX(this._bitsLabel.getLocX() / this.getScale() + 26);
        int heartLabelX = 20;
        int heartLabelY = 33;
        this._hungerLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "emptyHearts.png", this._mainDisplay, 62, 14, this.getScale());
        this._hungerLabel.setLoc(heartLabelX, heartLabelY);
        this._fullHunger = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fullHearts.png", this._mainDisplay, 62, 14, this.getScale());
        this._fullHunger.setLoc(heartLabelX, heartLabelY);
        this._exerciseLabel = new SpriteObj("", "", "", this._mainDisplay, 62, 14, this.getScale());
        this._exerciseLabel.setLoc(heartLabelX, heartLabelY);
        this._exerciseLabel.addAltSprite(this._hungerLabel.getAltSprite("emptyHearts"), "emptyHearts");
        this._exerciseLabel.setAltIcon("emptyHearts");
        this._fullExercise = new SpriteObj("", "", "", this._mainDisplay, 62, 14, this.getScale());
        this._fullExercise.setLoc(heartLabelX, heartLabelY);
        this._fullExercise.addAltSprite(this._fullHunger.getAltSprite("fullHearts"), "fullHearts");
        this._fullExercise.setAltIcon("fullHearts");
        this._typeLabel = new SpriteObj("", "", "", this._mainDisplay, 45, 21, this.getScale());
        this._typeLabel.setText("Elmnt.");
        this._typeLabel.setFont(this._bit);
        this._typeLabel.setForeground(Color.BLACK);
        this._attribute = new SpriteObj("", "", "", this._mainDisplay, 24, 24, this.getScale());
        this._attribute.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "null.png");
        this._fieldLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fields.png", this._mainDisplay, 14, 14, 4, (byte)(this.getScale() * 2));
        this._fieldLabel.addAltSprite(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "bits.png", (double)this.getScale() * 3.0), "bits");
        this._fieldLabel.setHorizontalAlignment(0);
        this._fieldLabel.addMouseListener(new MouseAdapter(){
            PhysicalState digimon;
            {
                this.digimon = SpriteAnim.this._controller.getModel().getDigimon();
            }

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.DNA_Inventory) {
                    if (SpriteAnim.this._controller.getModel().getDigimon().getIsHome()) {
                        if (this.digimon.getGrowthStage() == Enum.Stage.Egg || SpriteAnim.this.canInteract()) {
                            Enum.Field f = Enum.Field.values()[SpriteAnim.this._consumablePage];
                            if (this.digimon.getDNA().getOwned(f) > 0) {
                                SpriteAnim.this._controller.onFieldCharge();
                                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                            } else {
                                SpriteAnim.this._sounds.playSound(SoundConfig._error);
                            }
                        } else {
                            SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        }
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        SpriteAnim.this.setMessage("You can't charge DNA here");
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.DNA_Inventory) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._fieldLabel, 3, 3, 3, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.DNA_Inventory) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        this._elementLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "elements.png", this._mainDisplay, 22, 15, 1, (byte)(this.getScale() * 2));
        this._elementLabel.addAltSprite(this._attribute.getAltSprite("null"), "null");
        this._moodLabel = new SpriteObj("", "", "", this._mainDisplay, 24, 24, this.getScale());
        this._moodLabel.setLocX(105 - this._xPad);
        this._moodLabel.setLocY(54 - this._yPad);
        this._moodLabel.setBorder(null);
        this._moodLabel.setFont(this._bit.deriveFont((float)(60 * this.getScale())));
        this._moodLabel.setForeground(Color.BLACK);
        this._moodLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "happy.png");
        this._moodLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "happy2.png");
        this._moodLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "unhappy.png");
        this._moodLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "unhappy2.png");
        this._moodLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "depressed.png");
        this._moodLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "depressed2.png");
        this._energy = new SpriteObj("", "", "", this._mainDisplay, 36, 9, this.getScale());
        this._energy.setText("00/00");
        this._energy.setFont(this._bit.deriveFont((float)(16 * this.getScale())));
        this._energy.setForeground(Color.BLACK);
        this._energyLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "energy.png", this._mainDisplay, 104, 32, this.getScale());
        this._energyBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "energyBar.png", this._mainDisplay, 96, 8, this.getScale());
        this._energyBar.setHorizontalAlignment(2);
        this._recoveryLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleRecovery.png", this._mainDisplay, 18, 18, 2, this.getScale());
        this._recoveryLabel.setLoc(29 - this._xPad, 96 - this._yPad);
        this._sleepLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "sleep.png", this._mainDisplay, 14, 16, 2, this.getScale());
        this._ticLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "ticEmpty.png", this._mainDisplay, 40, 14, this.getScale());
        this._ticLabel.setLocX(90 - this._xPad);
        this._ticLabel.setLocY(95 - this._yPad);
        this._ticBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "tic.png", this._mainDisplay, 40, 14, this.getScale());
        this._ticBar.setLocX(90 - this._xPad);
        this._ticBar.setLocY(95 - this._yPad);
        this._agePanel = new JLabel();
        this._agePanel.setBorder(null);
        this._agePanel.setFont(this._bit);
        this._agePanel.setText(Integer.toString(this._controller.getModel().getDigimon().getAge()));
        this._agePanel.setBounds(27 - this._xPad * this.getScale(), 86 - this._yPad * this.getScale(), 80 * this.getScale(), ViewConfig._fontSize * this.getScale());
        this._agePanel.setForeground(Color.BLACK);
        this._mainDisplay.add(this._agePanel);
        this._weightPanel = new JLabel();
        this._weightPanel.setBorder(null);
        this._weightPanel.setFont(this._bit);
        this._weightPanel.setForeground(Color.BLACK);
        this._mainDisplay.add(this._weightPanel);
        this._weightLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weightNormal.png", this._mainDisplay, this.getScale());
        this._weightLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weightOver.png");
        this._weightLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weightUnder.png");
        this._favFoodLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "locked.png", this._mainDisplay, 24, 24, this.getScale());
        this._favFoodLabel.addAltSprite(this._attribute.getAltSprite("null"), "null");
        this._favFoodLabel.addMouseListener(new MouseAdapter(){
            PhysicalState digimon;
            {
                this.digimon = SpriteAnim.this._controller.getModel().getDigimon();
            }

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Intolerant && this.digimon.getFoodIntolerance().size() > 1) {
                    SpriteAnim.this._consumablePage++;
                    if (this.digimon.getFoodIntolerance().size() - 1 < SpriteAnim.this._consumablePage) {
                        SpriteAnim.this._consumablePage = 0;
                    }
                    SpriteAnim.this.setupFavFoodLabel(this.digimon.getFoodIntolerance().get(SpriteAnim.this._consumablePage));
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Intolerant && this.digimon.getFoodIntolerance().size() > 1) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._favFoodLabel, 3, 3, 3, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Intolerant && this.digimon.getFoodIntolerance().size() > 1) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        this._favFoodLabel.setHorizontalAlignment(0);
        this._favAttLabel = new SpriteObj("", "", "", this._mainDisplay, 28, 28, this.getScale());
        this._favAttLabel.addAltSprite(this._favFoodLabel.getAltSprite("locked"), "locked");
        this._favAttLabel.setAltIcon("locked");
        this._favAttLabel.addAltSprite(this._attribute.getAltSprite("null"), "null");
        this._favAttLabel.setHorizontalAlignment(0);
        this._favTimeLabel = new SpriteObj("", "", "", this._mainDisplay, 30, 30, this.getScale());
        this._favTimeLabel.addAltSprite(this._favFoodLabel.getAltSprite("locked"), "locked");
        this._favTimeLabel.setAltIcon("locked");
        this._favTimeLabel.addAltSprite(this._attribute.getAltSprite("null"), "null");
        this._favTimeLabel.setHorizontalAlignment(0);
        this._obedienceLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "obedienceBar.png", this._mainDisplay, 57, 14, this.getScale());
        this._obedienceLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "obedienceBarHalf.png");
        this._obedienceLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "obedienceBarFull.png");
        this._obedienceFull = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "obedienceFull.png", this._mainDisplay, 41, 6, this.getScale());
        this._obedienceFull.setHorizontalAlignment(2);
        this._vaccinePowerLabel = new SpriteObj("", "", "", this._mainDisplay, 31, 33, this.getScale());
        this._vaccinePowerLabel.setLocX(60 - this._xPad);
        this._vaccinePowerLabel.setLocY(50 - this._yPad);
        this._vaccinePowerLabel.setBorder(null);
        this._vaccinePowerLabel.setHorizontalAlignment(4);
        this._vaccinePowerLabel.setFont(this._bit);
        this._vaccinePowerLabel.setForeground(Color.BLACK);
        this._dataPowerLabel = new SpriteObj("", "", "", this._mainDisplay, 31, 33, this.getScale());
        this._dataPowerLabel.setLocX(this._vaccinePowerLabel.getLocX() / this.getScale());
        this._dataPowerLabel.setLocY(70 - this._yPad);
        this._dataPowerLabel.setBorder(null);
        this._dataPowerLabel.setHorizontalAlignment(4);
        this._dataPowerLabel.setFont(this._bit);
        this._dataPowerLabel.setForeground(Color.BLACK);
        this._virusPowerLabel = new SpriteObj("", "", "", this._mainDisplay, 31, 33, this.getScale());
        this._virusPowerLabel.setLocX(this._vaccinePowerLabel.getLocX() / this.getScale());
        this._virusPowerLabel.setLocY(90 - this._yPad);
        this._virusPowerLabel.setBorder(null);
        this._virusPowerLabel.setHorizontalAlignment(4);
        this._virusPowerLabel.setFont(this._bit);
        this._virusPowerLabel.setForeground(Color.BLACK);
        MouseAdapter tempListener = this.setupTempChangeListener();
        MouseAdapter tempMotion = this.setupTempChangeMotion();
        this._tempBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "tempBar.png", this._mainDisplay, 104, 59, this.getScale());
        this._tempBar.addMouseListener(tempListener);
        this._tempBar.addMouseMotionListener(tempMotion);
        this._currentTemp = new SpriteObj("", "", "", this._mainDisplay, 62, 31, this.getScale());
        this._currentTemp.setLoc(42, 38);
        this._currentTemp.setText("");
        this._currentTemp.setFont(this._bit);
        this._currentTemp.setForeground(Color.BLACK);
        this._tempArrow = new SpriteObj("", "", "", this._mainDisplay, 6, 12, this.getScale());
        this._tempArrow.addAltSprite(this._select.getAltSprite("select"), "select");
        this._tempArrow.addAltSprite(ViewUtil.flipIcon(this._select.getAltSprite("select")), "selectMirror");
        this._tempMoodArrow = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "tempArrow.png", this._mainDisplay, 24, 24, this.getScale());
        this._tempMoodArrow.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "tempArrow2.png");
        this._tempMoodArrow.setLocX(this._moodLabel.getLocX() / this.getScale() - this._tempMoodArrow.getSizeX() / this.getScale());
        this._tempMoodArrow.setLocY(this._moodLabel.getLocY() / this.getScale());
    }

    private void initFeedMenu() {
        this._meatButton = new SpriteObj("", "", "", this._mainInteract, 24, 24, this.getScale());
        this._meatButton.setLocX(56 - this._xPad);
        this._meatButton.setLocY(57 - this._yPad);
        this._meatButton.addMouseListener(new MouseAdapter(){
            PhysicalState digimon;
            {
                this.digimon = SpriteAnim.this._controller.getModel().getDigimon();
            }

            @Override
            public void mousePressed(MouseEvent e) {
                boolean clickOK = true;
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Medical: {
                        SpriteAnim.this._itemType = SpriteAnim.this._controller.getModel().getDigimon().getItemByID(80);
                        SpriteAnim.this._controller.onUseMedItem();
                        break;
                    }
                    case Feed_Validation: {
                        SpriteAnim.this._foodType = SpriteAnim.this._controller.getModel().getDigimon().getFoodByID(0);
                        if (SpriteAnim.this.canInteract() && SpriteAnim.this._foodType.getCurrentUses() > 0 && this.digimon.careEffectCanApply(SpriteAnim.this._foodType)) {
                            SpriteAnim.this._controller.onFeed(SpriteAnim.this._foodType);
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Food_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellFood();
                        break;
                    }
                    case Item_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellItem();
                        break;
                    }
                    case Food_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseFood();
                        break;
                    }
                    case Food_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyFood();
                        break;
                    }
                    case Buy_Food: {
                        if (SpriteAnim.this._consumableType.isAvailable()) {
                            SpriteAnim.this._controller.onFoodPurchase();
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Sell_Food: {
                        SpriteAnim.this._controller.onFoodSale();
                        break;
                    }
                    case Use_Food: 
                    case Use_Med_Food: 
                    case Use_Med_Item: {
                        if (SpriteAnim.this.canInteract() && this.digimon.careEffectCanApply(SpriteAnim.this._foodType)) {
                            switch (SpriteAnim.this._controller.getCurrentMenu()) {
                                case Use_Food: {
                                    SpriteAnim.this._controller.onFeed(SpriteAnim.this._foodType);
                                    break;
                                }
                                case Use_Med_Food: {
                                    if (SpriteAnim.this._foodType.getID() == 5 && SpriteAnim.this._foodType.getCurrentUses() > 0) {
                                        SpriteAnim.this._controller.onVitamin(SpriteAnim.this._foodType);
                                        break;
                                    }
                                    if (SpriteAnim.this._foodType.getID() == 4 && SpriteAnim.this._foodType.getCurrentUses() > 0 && this.digimon.isSick()) {
                                        SpriteAnim.this._controller.onMed(SpriteAnim.this._foodType);
                                        break;
                                    }
                                    clickOK = false;
                                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                                    break;
                                }
                                case Use_Med_Item: {
                                    if (this.digimon.isInj() && SpriteAnim.this._itemType.getCurrentUses() > 0) {
                                        SpriteAnim.this._controller.onBandage(SpriteAnim.this._itemType);
                                        break;
                                    }
                                    clickOK = false;
                                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                                }
                            }
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Item_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyItem();
                        break;
                    }
                    case Item_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseItem();
                        break;
                    }
                    case Buy_Item: {
                        if (SpriteAnim.this._consumableType.isAvailable()) {
                            SpriteAnim.this._controller.onItemPurchase();
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Sell_Item: {
                        SpriteAnim.this._controller.onItemSale();
                        break;
                    }
                    case Use_Item: 
                    case UseEvolutionItem: {
                        if (SpriteAnim.this.canInteract() && this.digimon.careEffectCanApply(SpriteAnim.this._itemType)) {
                            clickOK = SpriteAnim.this._controller.onItemUse(SpriteAnim.this._itemType);
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case EvolutionInventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._meatButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseEvolutionItem();
                    }
                }
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Medical: {
                        if (!this.digimon.isInj()) {
                            SpriteAnim.this._sounds.playSound(SoundConfig._error);
                            break;
                        }
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        break;
                    }
                    case DNA_Stats: {
                        break;
                    }
                    default: {
                        if (!clickOK || SpriteAnim.this._controller.getCurrentState() == Enum.State.ReturnItem || SpriteAnim.this._controller.getCurrentState() == Enum.State.Gifting) break;
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentState() != Enum.State.ReturnItem && SpriteAnim.this._controller.getCurrentState() != Enum.State.Gifting && SpriteAnim.this._controller.getCurrentMenu() != Enum.Menu.DNA_Stats) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._meatButton, 3, 3, 3, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._border.setVisible(false);
            }
        });
        this._fishButton = new SpriteObj("", "", "", this._mainInteract, 24, 24, this.getScale());
        this._fishButton.setLocX(27 - this._xPad + this._meatButton.getSizeX() / this.getScale() + 37 + this._select.getSizeX() / this.getScale());
        this._fishButton.setLocY(57 - this._yPad);
        this._fishButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                boolean clickOK = true;
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Medical: {
                        SpriteAnim.this._foodType = SpriteAnim.this._controller.getModel().getDigimon().getFoodByID(4);
                        SpriteAnim.this._controller.onUseMedFood();
                        break;
                    }
                    case Feed_Validation: {
                        SpriteAnim.this._foodType = SpriteAnim.this._controller.getModel().getDigimon().getFoodByID(1);
                        if (SpriteAnim.this.canInteract() && SpriteAnim.this._foodType.getCurrentUses() > 0 && digimon.careEffectCanApply(SpriteAnim.this._foodType)) {
                            SpriteAnim.this._controller.onFeed(SpriteAnim.this._foodType);
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Food_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fishButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellFood();
                        break;
                    }
                    case Item_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fishButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellItem();
                        break;
                    }
                    case Food_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fishButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseFood();
                        break;
                    }
                    case Food_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fishButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyFood();
                        break;
                    }
                    case Item_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fishButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyItem();
                        break;
                    }
                    case Item_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fishButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseItem();
                    }
                }
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Medical: {
                        if (!digimon.isSick()) {
                            SpriteAnim.this._sounds.playSound(SoundConfig._error);
                            break;
                        }
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        break;
                    }
                    default: {
                        if (!clickOK) break;
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this.setBorder(SpriteAnim.this._fishButton, 3, 3, 3, true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._border.setVisible(false);
            }
        });
        this._fruitButton = new SpriteObj("", "", "", this._mainInteract, 24, 24, this.getScale());
        this._fruitButton.setLocX(56 - this._xPad);
        this._fruitButton.setLocY(58 - this._yPad + this._meatButton.getSizeY() / this.getScale());
        this._fruitButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                boolean clickOK = true;
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Medical: {
                        SpriteAnim.this._foodType = SpriteAnim.this._controller.getModel().getDigimon().getFoodByID(5);
                        SpriteAnim.this._controller.onUseMedFood();
                        break;
                    }
                    case Feed_Validation: {
                        SpriteAnim.this._foodType = SpriteAnim.this._controller.getModel().getDigimon().getFoodByID(2);
                        if (SpriteAnim.this.canInteract() && SpriteAnim.this._foodType.getCurrentUses() > 0 && digimon.careEffectCanApply(SpriteAnim.this._foodType)) {
                            SpriteAnim.this._controller.onFeed(SpriteAnim.this._foodType);
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Food_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fruitButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellFood();
                        break;
                    }
                    case Item_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fruitButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellItem();
                        break;
                    }
                    case Food_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fruitButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseFood();
                        break;
                    }
                    case Food_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fruitButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyFood();
                        break;
                    }
                    case Item_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fruitButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyItem();
                        break;
                    }
                    case Item_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._fruitButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseItem();
                    }
                }
                if (clickOK) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this.setBorder(SpriteAnim.this._fruitButton, 3, 3, 3, true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._border.setVisible(false);
            }
        });
        this._vegButton = new SpriteObj("", "", "", this._mainInteract, 24, 24, this.getScale());
        this._vegButton.setLocX(64 - this._xPad + this._fruitButton.getSizeX() / this.getScale() + this._select.getSizeX() / this.getScale());
        this._vegButton.setLocY(58 - this._yPad + this._fishButton.getSizeY() / this.getScale());
        this._vegButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                boolean clickOK = true;
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Feed_Validation: {
                        SpriteAnim.this._foodType = SpriteAnim.this._controller.getModel().getDigimon().getFoodByID(3);
                        if (SpriteAnim.this.canInteract() && SpriteAnim.this._foodType.getCurrentUses() > 0 && digimon.careEffectCanApply(SpriteAnim.this._foodType)) {
                            SpriteAnim.this._controller.onFeed(SpriteAnim.this._foodType);
                            break;
                        }
                        clickOK = false;
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case Food_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._vegButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellFood();
                        break;
                    }
                    case Item_Inventory_Sell: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._vegButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onSellItem();
                        break;
                    }
                    case Food_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._vegButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseFood();
                        break;
                    }
                    case Food_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._vegButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyFood();
                        break;
                    }
                    case Item_Shop: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._vegButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onBuyItem();
                        break;
                    }
                    case Item_Inventory: {
                        SpriteAnim.this.assignConsumableTypes(SpriteAnim.this._vegButton, SpriteAnim.this._controller.getCurrentMenu());
                        SpriteAnim.this._controller.onUseItem();
                    }
                }
                if (clickOK) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this.setBorder(SpriteAnim.this._vegButton, 3, 3, 3, true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._border.setVisible(false);
            }
        });
        this._inventoryButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "inventory.png", this._mainInteract, 14, 18, this.getScale());
        this._inventoryButton.addAltSprite(ViewUtil.getTransparentImage(this._inventoryButton.getAltSprite("inventory"), 0.25f), "tInventory");
        this._inventoryButton.setAltIcon("tInventory");
        this._inventoryButton.setLocX(32 - this._xPad);
        this._inventoryButton.setLocY(72 - this._yPad);
        this._inventoryButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onInventory();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._inventoryButton.setAltIcon("inventory");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._inventoryButton.setAltIcon("tInventory");
            }
        });
        this._foodShopButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "foodShop.png", this._mainInteract, 22, 16, this.getScale());
        this._foodShopButton.addAltSprite(ViewUtil.getTransparentImage(this._foodShopButton.getAltSprite("foodShop"), 0.25f), "tFoodShop");
        this._foodShopButton.setAltIcon("tFoodShop");
        this._foodShopButton.setLocX(28 - this._xPad);
        this._foodShopButton.setLocY(94 - this._yPad);
        this._foodShopButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getModel().getDigimon().getAmenitiesOpen()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onShop();
                } else {
                    if (!SpriteAnim.this._controller.getModel().getDigimon().getIsHome()) {
                        SpriteAnim.this.setMessage("There are no shops in the wilderness");
                    }
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._foodShopButton.setAltIcon("foodShop");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._foodShopButton.setAltIcon("tFoodShop");
            }
        });
        this._consumableDescription = new SpriteObj("", "", "", this._mainDisplay, 104, 60, this.getScale());
        this._consumableDescription.setLocX(27 - this._xPad);
        this._consumableDescription.setLocY(0);
        this._consumableDescription.setBorder(null);
        this._consumableDescription.setFont(this._bit.deriveFont((float)(16 * this.getScale())));
        this._consumableDescription.setForeground(Color.BLACK);
        this._messageDisplay = new SpriteObj("", "", "", this._mainDisplay, 104, 60, this.getScale());
        this._messageDisplay.setLocX(27 - this._xPad);
        this._messageDisplay.setLocY(0);
        this._messageDisplay.setBorder(null);
        this._messageDisplay.setFont(this._bit.deriveFont((float)(24 * this.getScale())));
        this._messageDisplay.setForeground(Color.BLACK);
        this._habitatLabel = new SpriteObj("", "", "", this._mainDisplay, 75, 18, this.getScale());
        this._habitatLabel.setLocX(50 - this._xPad);
        this._habitatLabel.setLocY(68 - this._yPad);
        this._habitatLabel.setBorder(null);
        this._habitatLabel.setFont(this._bit);
        this._habitatLabel.setForeground(Color.BLACK);
        this._habitatLabel.setText("Habitats");
        this._habitatLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().equals((Object)Enum.Menu.Shop_Validation) || SpriteAnim.this._controller.getModel().getDigimon().getAmenitiesOpen()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._habitat = -1;
                    SpriteAnim.this._controller.onHabitat();
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._habitatLabel.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._habitatLabel.getSizeX() / SpriteAnim.this.getScale() - 6);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._habitatLabel.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._itemOption = new SpriteObj("", "", "", this._mainDisplay, 60, 18, this.getScale());
        this._itemOption.setLocX(50 - this._xPad);
        this._itemOption.setLocY(87 - this._yPad);
        this._itemOption.setBorder(null);
        this._itemOption.setFont(this._bit);
        this._itemOption.setForeground(Color.BLACK);
        this._itemOption.setText("Items");
        this._itemOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onItem();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._itemOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._itemOption.getSizeX() / SpriteAnim.this.getScale() - 6);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._itemOption.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._proteinBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "nutritionProtein.png", this._mainInteract, 15, 42, this.getScale());
        this._proteinBar.setLoc(28, 17);
        this._mineralBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "nutritionMineral.png", this._mainInteract, 15, 42, this.getScale());
        this._mineralBar.setLoc(8 + this._proteinBar.getSizeX() / this.getScale() + this._proteinBar.getLocX() / this.getScale(), this._proteinBar.getLocY() / this.getScale());
        this._vitaminBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "nutritionVitamin.png", this._mainInteract, 15, 42, this.getScale());
        this._vitaminBar.setLoc(8 + this._mineralBar.getSizeX() / this.getScale() + this._mineralBar.getLocX() / this.getScale(), this._proteinBar.getLocY() / this.getScale());
    }

    private void initPraiseMenu() {
        this._praiseButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "praise.png", this._mainInteract, 28, 28, this.getScale());
        this._praiseButton.setLocX(52 - this._xPad);
        this._praiseButton.setLocY(71 - this._yPad);
        this._praiseButton.addAltSprite(ViewUtil.getTransparentImage(this._praiseButton.getAltSprite("praise"), 0.25f), "praiseTransp");
        this._praiseButton.setAltIcon("praiseTransp");
        this._praiseButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "restart.png");
        this._praiseButton.addAltSprite(ViewUtil.getTransparentImage(this._praiseButton.getAltSprite("restart"), 0.25f), "tRestart");
        this._praiseButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getAlive()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onPraise();
                    SpriteAnim.this._praiseButton.setAltIcon("tRestart");
                } else if (SpriteAnim.this.canInteract()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onPraise();
                    SpriteAnim.this._praiseButton.setAltIcon("praiseTransp");
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getAlive()) {
                    SpriteAnim.this._praiseButton.setAltIcon("restart");
                } else {
                    SpriteAnim.this._praiseButton.setAltIcon("praise");
                }
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getAlive()) {
                    SpriteAnim.this._praiseButton.setAltIcon("tRestart");
                } else {
                    SpriteAnim.this._praiseButton.setAltIcon("praiseTransp");
                }
            }
        });
        this._scoldButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "scold.png", this._mainInteract, 28, 28, this.getScale());
        this._scoldButton.setLocX(this._praiseButton.getLocX() / this.getScale() + 37);
        this._scoldButton.setLocY(this._praiseButton.getLocY() / this.getScale());
        this._scoldButton.addAltSprite(ViewUtil.getTransparentImage(this._scoldButton.getAltSprite("scold"), 0.25f), "scoldTransp");
        this._scoldButton.setAltIcon("scoldTransp");
        this._scoldButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this.canInteract()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._scoldButton.setAltIcon("scoldTransp");
                    SpriteAnim.this._controller.onScold();
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._scoldButton.setAltIcon("scold");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._scoldButton.setAltIcon("scoldTransp");
            }
        });
    }

    private void setBorder(SpriteObj o, int xPad, int yPad, int girth, boolean visible) {
        this._border.setBounds(o.getLocX() - xPad * this.getScale() + 1 * this.getScale(), o.getLocY() - yPad * this.getScale() + 1 * this.getScale(), o.getSizeX() + xPad * 2 * this.getScale() - 2 * this.getScale(), o.getSizeY() + yPad * 2 * this.getScale() - 2 * this.getScale());
        this._border.setVisible(visible);
        this._border.repaint();
    }

    private void updateBorder(SpriteObj o, int xPad, int yPad) {
        this._border.setBounds(o.getLocX() - xPad * this.getScale(), o.getLocY() - yPad * this.getScale(), o.getSizeX() + xPad * 2 * this.getScale(), o.getSizeY() + yPad * 2 * this.getScale());
    }

    private void initExerciseMenu() {
        this._rateLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "dnaRate.png", this._mainDisplay, 100, 28, this.getScale());
        this._rate = new SpriteObj("", "", "", this._mainDisplay, 31, 31, this.getScale());
        this._rate.setText("99");
        this._rate.setFont(this._bit.deriveFont((float)(31 * this.getScale())));
        this._rate.setForeground(Color.BLACK);
        this._hitButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainButton.png", this._mainInteract, 20, 20, this.getScale());
        this._hitButton.setLocX(70 - this._xPad);
        this._hitButton.setLocY(85 - this._yPad);
        this._hitButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainButtonPressed.png");
        this._hitButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._hitButton);
                SpriteAnim.this._hitButton.setAltIcon("trainButtonPressed");
                if (SpriteAnim.this._currentAnim == Enum.State.Vaccine_Training || SpriteAnim.this._currentAnim == Enum.State.Virus_Training || SpriteAnim.this._currentAnim == Enum.State.DNA_Generate) {
                    SpriteAnim.this._controller.onHit(SpriteAnim.this._currentAnim);
                }
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                SpriteAnim.this._hitButton.setAltIcon("trainButton");
            }
        });
        this._hitLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainHit.png", this._mainDisplay, 52, 20, this.getScale());
        this._hitLabel.setLocX(57 - this._xPad);
        this._hitLabel.setLocY(60 - this._yPad);
        this._shieldBot = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainShield.png", this._mainInteract, 16, 18, this.getScale());
        this._shieldBot.setLocX(90 - this._xPad);
        this._shieldBot.setLocY(90 - this._yPad);
        this._shieldBot.addAltSprite(ViewUtil.getTransparentImage(this._shieldBot.getAltSprite("trainShield"), 0.25f), "shieldTransp");
        this._shieldBot.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._started) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onShield();
                    SpriteAnim.this.checkShield();
                }
            }
        });
        this._shieldTop = new SpriteObj("", "", "", this._mainInteract, 16, 18, this.getScale());
        this._shieldTop.setLocX(90 - this._xPad);
        this._shieldTop.setLocY(61 - this._yPad);
        this._shieldTop.addAltSprite(this._shieldBot.getAltSprite("trainShield"), "trainShield");
        this._shieldTop.addAltSprite(this._shieldBot.getAltSprite("shieldTransp"), "shieldTransp");
        this._shieldTop.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._started) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onShield();
                    SpriteAnim.this.checkShield();
                }
            }
        });
        this._trainBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainBarEmpty.png", this._mainDisplay, 102, 12, this.getScale());
        this._trainBar.setLocX(28 - this._xPad);
        this._trainBar.setLocY(70 - this._yPad);
        this._trainBarFull = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainBar.png", this._mainDisplay, 94, 4, this.getScale());
        this._trainBarFull.setLocX(32 - this._xPad);
        this._trainBarFull.setLocY(74 - this._yPad);
        this._attackSprite = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attackSprites.png", this._mainDisplay, 24, 24, 3, this.getScale());
        this._attackSprite.setVerticalAlignment(1);
        this._attackSprite.setLocX(-100);
        this._attackSprite.setLocY(this._character.getLocY() / this.getScale());
        this._specialAttacks = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attackSpritesSpecial.png", null, 24, 24, 3, this.getScale());
    }

    private void initBattleMenu(Icon icon) {
        int i;
        this._battleFlash = new SpriteObj("", "", "", this._mainInteract, 105, 60, this.getScale());
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleStart.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleStartFlash.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "jogressStart.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "jogressStartFlash.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleConnectStart.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleConnectStartFlash.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "jogressConnectStart.png");
        this._battleFlash.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "jogressConnectStartFlash.png");
        this._battleFlash.setLocX(26 - this._xPad);
        this._battleFlash.setLocY(0);
        this._battleFlash.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                if (SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.Battle_Flash)) {
                    SpriteAnim.this.endAnim();
                    SpriteAnim.this._controller.onBattleFlash();
                } else {
                    SpriteAnim.this.endAnim();
                    SpriteAnim.this._controller.onJogress();
                }
                SpriteAnim.this.disposeMusic();
            }
        });
        this._battleBags = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "battleBags.png", this._mainDisplay, 40, 52, 6, this.getScale());
        this._opponent.setVerticalAlignment(3);
        this._battleBags.setLocX(27 - this._xPad);
        this._battleBags.setLocY(50 - this._yPad);
        this._opponent.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "punchingBag.png");
        this._opponent.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "punchingBagBroken.png");
        this._opponent.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainGreen.png");
        this._opponent.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "trainGreenUp.png");
        this._battleOption = new SpriteObj("", "", "", this._mainInteract, 32, 18, this.getScale());
        this._battleOption.setText("VS");
        this._battleOption.setFont(this._bit);
        this._battleOption.setForeground(Color.BLACK);
        this._battleOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onVS();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._battleOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._battleOption.getSizeX() / SpriteAnim.this.getScale() + 6);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._battleOption.getLocY() / SpriteAnim.this.getScale() + 1);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._cardsOption = new SpriteObj("", "", "", this._mainInteract, 58, 21, this.getScale());
        this._cardsOption.setText("Cards");
        this._cardsOption.setFont(this._bit);
        this._cardsOption.setForeground(Color.BLACK);
        this._cardsOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case DNA_Validation: {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onCardOption();
                        break;
                    }
                    default: {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onCardOption();
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._cardsOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._cardsOption.getSizeX() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._cardsOption.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._collection = new SpriteObj("", "", "", this._mainInteract, 90, 18, this.getScale());
        this._collection.setText("Collection");
        this._collection.setFont(this._bit);
        this._collection.setForeground(Color.BLACK);
        this._collection.setLocX(42 - this._xPad);
        this._collection.setLocY(86 - this._yPad);
        this._collection.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._error);
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._collection.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._collection.getSizeX() / SpriteAnim.this.getScale() - 9);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._collection.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._cardShop = new SpriteObj("", "", "", this._mainInteract, 50, 18, this.getScale());
        this._cardShop.setText("Shop");
        this._cardShop.setFont(this._bit);
        this._cardShop.setForeground(Color.BLACK);
        this._cardShop.setLocX(58 - this._xPad);
        this._cardShop.setLocY(62 - this._yPad);
        this._cardShop.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getModel().getDigimon().getAmenitiesOpen()) {
                    SpriteAnim.this._controller.onCardShop();
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                } else {
                    if (!SpriteAnim.this._controller.getModel().getDigimon().getIsHome()) {
                        SpriteAnim.this.setMessage("There are no shops in the wilderness");
                    }
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._cardShop.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._cardShop.getSizeX() / SpriteAnim.this.getScale());
                SpriteAnim.this._select.setLocY(SpriteAnim.this._cardShop.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._jogressOption = new SpriteObj("", "", "", this._mainInteract, 78, 24, this.getScale());
        this._jogressOption.setText("Jogress");
        this._jogressOption.setFont(this._bit);
        this._jogressOption.setForeground(Color.BLACK);
        this._jogressOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                switch (SpriteAnim.this._controller.getCurrentMenu()) {
                    case Battle_Validation: {
                        if (SpriteAnim.this.canInteract() && SpriteAnim.this._controller.getModel().getDigimon().getAmenitiesOpen()) {
                            SpriteAnim.this._controller.canJogress();
                            break;
                        }
                        if (!SpriteAnim.this._controller.getModel().getDigimon().getIsHome()) {
                            SpriteAnim.this.setMessage("You can only do this at home or in town");
                        }
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    case DNA_Validation: {
                        if (SpriteAnim.this._controller.getModel().getDigimon().getGrowthStage() == Enum.Stage.Egg || SpriteAnim.this.canInteract()) {
                            SpriteAnim.this._sounds.playSound(SoundConfig._click);
                            SpriteAnim.this._controller.onMultiOption();
                            break;
                        }
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                        break;
                    }
                    default: {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onMultiOption();
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._jogressOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._jogressOption.getSizeX() / SpriteAnim.this.getScale());
                SpriteAnim.this._select.setLocY(SpriteAnim.this._jogressOption.getLocY() / SpriteAnim.this.getScale() + 4);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._tourneyOption = new SpriteObj("", "", "", this._mainInteract, 80, 24, this.getScale());
        this._tourneyOption.setText("Tourney");
        this._tourneyOption.setFont(this._bit);
        this._tourneyOption.setForeground(Color.BLACK);
        this._tourneyOption.setLocX(46 - this._xPad);
        this._tourneyOption.setLocY(54 - this._yPad);
        this._tourneyOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onTourneyOption();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._tourneyOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._tourneyOption.getSizeX() / SpriteAnim.this.getScale() - 6);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._tourneyOption.getLocY() / SpriteAnim.this.getScale() + 4);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._tourneyRecords = new SpriteObj("", "", "", this._mainInteract, 77, 18, this.getScale());
        this._tourneyRecords.setText("Records");
        this._tourneyRecords.setFont(this._bit);
        this._tourneyRecords.setForeground(Color.BLACK);
        this._tourneyRecords.setLocX(48 - this._xPad);
        this._tourneyRecords.setLocY(62 - this._yPad);
        this._tourneyRecords.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onTourneyRecords();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._tourneyRecords.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._tourneyRecords.getSizeX() / SpriteAnim.this.getScale() - 5);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._tourneyRecords.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._seasonRecords = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "seasons.png", this._mainDisplay, 57, 57, this.getScale());
        this._seasonRecords.setLoc(50 - this._xPad, 55 - this._yPad);
        this._springRecords = new SpriteObj("", "", "", this._mainInteract, 21, 21, this.getScale());
        this._springRecords.setLoc(53 - this._xPad, 58 - this._yPad);
        this._springRecords.addAltSprite(this._seasonLabel.getAltSprite("spring"), "spring");
        this._springRecords.addAltSprite(ViewUtil.getTransparentImage(this._seasonLabel.getAltSprite("spring"), 0.5f), "tSpring");
        this._springRecords.setAltIcon("tSpring");
        this._springRecords.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._controller.onSeasonRecords(Enum.Season.Spring);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._springRecords.setAltIcon("spring");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._springRecords.setAltIcon("tSpring");
                }
            }
        });
        this._summerRecords = new SpriteObj("", "", "", this._mainInteract, 21, 21, this.getScale());
        this._summerRecords.setLoc(83 - this._xPad, 58 - this._yPad);
        this._summerRecords.addAltSprite(this._seasonLabel.getAltSprite("summer"), "summer");
        this._summerRecords.addAltSprite(ViewUtil.getTransparentImage(this._seasonLabel.getAltSprite("summer"), 0.5f), "tSummer");
        this._summerRecords.setAltIcon("tSummer");
        this._summerRecords.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._controller.onSeasonRecords(Enum.Season.Summer);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._summerRecords.setAltIcon("summer");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._summerRecords.setAltIcon("tSummer");
                }
            }
        });
        this._fallRecords = new SpriteObj("", "", "", this._mainInteract, 21, 21, this.getScale());
        this._fallRecords.setLoc(53 - this._xPad, 88 - this._yPad);
        this._fallRecords.addAltSprite(this._seasonLabel.getAltSprite("fall"), "fall");
        this._fallRecords.addAltSprite(ViewUtil.getTransparentImage(this._seasonLabel.getAltSprite("fall"), 0.5f), "tFall");
        this._fallRecords.setAltIcon("tFall");
        this._fallRecords.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._controller.onSeasonRecords(Enum.Season.Fall);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._fallRecords.setAltIcon("fall");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._fallRecords.setAltIcon("tFall");
                }
            }
        });
        this._winterRecords = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "winter.png", this._mainInteract, 21, 21, this.getScale());
        this._winterRecords.setLoc(83 - this._xPad, 88 - this._yPad);
        this._winterRecords.addAltSprite(this._seasonLabel.getAltSprite("winter"), "winter");
        this._winterRecords.addAltSprite(ViewUtil.getTransparentImage(this._seasonLabel.getAltSprite("winter"), 0.5f), "tWinter");
        this._winterRecords.setAltIcon("tWinter");
        this._winterRecords.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._controller.onSeasonRecords(Enum.Season.Winter);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._winterRecords.setAltIcon("winter");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getCurrentMenu().toString().contains("Prelim")) {
                    SpriteAnim.this._winterRecords.setAltIcon("tWinter");
                }
            }
        });
        this._tourneyEnter = new SpriteObj("", "", "", this._mainInteract, 55, 18, this.getScale());
        this._tourneyEnter.setText("Enter");
        this._tourneyEnter.setFont(this._bit);
        this._tourneyEnter.setForeground(Color.BLACK);
        this._tourneyEnter.setLocX(58 - this._xPad);
        this._tourneyEnter.setLocY(86 - this._yPad);
        this._tourneyEnter.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getModel().getDigimon().getAmenitiesOpen()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onTourneyEnter();
                    SpriteAnim.this.checkTrophyNum();
                } else {
                    if (!SpriteAnim.this._controller.getModel().getDigimon().getIsHome()) {
                        SpriteAnim.this.setMessage("There are no colosseums in the wilderness");
                    }
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._tourneyEnter.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._tourneyEnter.getSizeX() / SpriteAnim.this.getScale() - 6);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._tourneyEnter.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        for (i = 0; i < this._trophies.length; ++i) {
            final int currentIndex = i;
            this._trophies[i] = new SpriteObj("", "", "", this._mainInteract, 18, 18, this.getScale());
            if (currentIndex == 1) {
                this._trophies[currentIndex].setName("Prelim");
            }
            this._trophies[i].setVisible(false);
            this._trophies[i].addMouseListener(new MouseAdapter(this){
                final /* synthetic */ SpriteAnim this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void mousePressed(MouseEvent e) {
                    PhysicalState digimon = this.this$0._controller.getModel().getDigimon();
                    Enum.State state = digimon.getCurrentState();
                    if (state != Enum.State.Tourney_Start && state != Enum.State.Tourney_Trophy) {
                        Enum.Menu menu = this.this$0._controller.getCurrentMenu();
                        if (this.this$0._trophies[currentIndex].getName() != null && this.this$0._trophies[currentIndex].getName().equals("Prelim") && (menu == Enum.Menu.Tourney_Registration || menu == Enum.Menu.TrophyDetails || menu == Enum.Menu.Registration_Prelim_Details || menu == Enum.Menu.Records_Prelim_Details)) {
                            this.this$0._controller.onPrelimDetails();
                            this.this$0._sounds.playSound(SoundConfig._click);
                        } else if (menu != Enum.Menu.Tourney_Enter && menu != Enum.Menu.Tourney_Registration && menu != Enum.Menu.TrophyDetails && menu != Enum.Menu.Royale_Lineup && menu != Enum.Menu.Registration_Prelim_Details && menu != Enum.Menu.Records_Prelim_Details) {
                            Trophy trophy;
                            int trophyIndex = currentIndex + this.this$0._trophyPage * ViewConfig._trophyRecordsPageSize;
                            int trophySet = 0;
                            if (trophyIndex >= 100) {
                                trophySet = trophyIndex % 100;
                                trophyIndex -= trophySet * 100;
                            }
                            if ((trophy = this.this$0._controller.checkTrophy(trophyIndex, trophySet)) == null || !trophy.getEarned()) {
                                this.this$0._sounds.playSound(SoundConfig._error);
                            } else {
                                if (menu.toString().contains("Record")) {
                                    this.this$0._sounds.playSound(SoundConfig._click);
                                }
                                this.this$0._trophyInSchedule = trophy.getID();
                                this.this$0._controller.onTrophyDetails(trophy);
                            }
                        } else if (this.this$0._controller.getCurrentMenu() == Enum.Menu.Tourney_Enter) {
                            Trophy trophy = this.this$0.getCurrentSelectedTrophy(digimon);
                            if (trophy == null) {
                                this.this$0._sounds.playSound(SoundConfig._error);
                            } else {
                                if (menu == Enum.Menu.Tourney_Enter) {
                                    this.this$0._sounds.playSound(SoundConfig._click);
                                }
                                this.this$0._controller.onTrophyDetails(trophy);
                            }
                        }
                    }
                }

                @Override
                public void mouseEntered(MouseEvent e) {
                    Enum.Menu menu = this.this$0._controller.getCurrentMenu();
                    if (menu != Enum.Menu.TrophyDetails && menu != Enum.Menu.Registration_Prelim_Details && menu != Enum.Menu.Records_Prelim_Details && menu == Enum.Menu.Tourney_Enter && this.this$0._controller.getModel().getDigimon().getCurrentState() != Enum.State.Tourney_Start || menu.toString().contains("Records") && !menu.toString().contains("Prelim") || this.this$0._trophies[currentIndex].getName() != null && this.this$0._trophies[currentIndex].getName().equals("Prelim") && (menu == Enum.Menu.Tourney_Registration || menu == Enum.Menu.TrophyDetails || menu == Enum.Menu.Registration_Prelim_Details || menu == Enum.Menu.Records_Prelim_Details)) {
                        this.this$0.setBorder(this.this$0._trophies[currentIndex], 1, 3, 3, true);
                        this.this$0._sounds.playSound(SoundConfig._select);
                    }
                }

                @Override
                public void mouseExited(MouseEvent e) {
                    Enum.Menu menu = this.this$0._controller.getCurrentMenu();
                    if (menu != Enum.Menu.TrophyDetails && menu != Enum.Menu.Registration_Prelim_Details && menu != Enum.Menu.Records_Prelim_Details && menu == Enum.Menu.Tourney_Enter && this.this$0._controller.getModel().getDigimon().getCurrentState() != Enum.State.Tourney_Start || menu.toString().contains("Records") && !menu.toString().contains("Prelim") || this.this$0._trophies[currentIndex].getName() != null && this.this$0._trophies[currentIndex].getName().equals("Prelim") && (menu == Enum.Menu.Tourney_Registration || menu == Enum.Menu.TrophyDetails || menu == Enum.Menu.Registration_Prelim_Details || menu == Enum.Menu.Records_Prelim_Details)) {
                        this.this$0._border.setVisible(false);
                    }
                }
            });
        }
        this._availableHours = new SpriteObj("", "", "", this._mainDisplay, 100, 40, this.getScale());
        this._availableHours.setLocX(0);
        this._availableHours.setLocY(90 - this._yPad);
        this._availableHours.setBorder(null);
        this._availableHours.setFont(this._bit);
        this._availableHours.setForeground(Color.BLACK);
        this._roster = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "roster.png", this._mainDisplay, 101, 42, this.getScale());
        this._royaleLineup = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "royale.png", this._mainDisplay, 98, 56, this.getScale());
        this._participants = new SpriteObj[8];
        for (i = 0; i < this._participants.length; ++i) {
            this._participants[i] = new SpriteObj("", "", "", this._mainDisplay, 16, 16, this.getScale());
            this._participants[i].addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "zoneComplete.png");
        }
        this._participants[0].addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onOpponent();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._participants[0], 1, 1, 1, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        this._royaleNum = new SpriteObj("", "", "", this._mainDisplay, 90, 31, this.getScale());
        this._royaleNum.setBorder(null);
        this._royaleNum.setFont(this._bit.deriveFont((float)(15.5 * (double)this.getScale())));
        this._royaleNum.setForeground(Color.BLACK);
        this._multiOption = new SpriteObj("", "", "", this._mainInteract, 50, 18, this.getScale());
        this._multiOption.setText("Multi");
        this._multiOption.setFont(this._bit);
        this._multiOption.setForeground(Color.BLACK);
        this._multiOption.setLocX(61 - this._xPad);
        this._multiOption.setLocY(77 - this._yPad);
        this._multiOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getModel().getDigimon().getAmenitiesOpen()) {
                    if (SpriteAnim.this._controller.onMultiOption()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else {
                    if (!SpriteAnim.this._controller.getModel().getDigimon().getIsHome()) {
                        SpriteAnim.this.setMessage("You can only do this at home or in town");
                    }
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._multiOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._multiOption.getSizeX() / SpriteAnim.this.getScale() + 8);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._multiOption.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._hostOption = new SpriteObj("", "", "", this._mainInteract, 50, 18, this.getScale());
        this._hostOption.setText("Host");
        this._hostOption.setFont(this._bit);
        this._hostOption.setForeground(Color.BLACK);
        this._hostOption.setLocX((int)Math.floor(52.0) + 8 - this._xPad);
        this._hostOption.setLocY(62 - this._yPad);
        this._hostOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onHost();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._hostOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._hostOption.getSizeX() / SpriteAnim.this.getScale() + 4);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._hostOption.getLocY() / SpriteAnim.this.getScale() + 1);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._connectOption = new SpriteObj("", "", "", this._mainInteract, 75, 18, this.getScale());
        this._connectOption.setText("Connect");
        this._connectOption.setFont(this._bit);
        this._connectOption.setForeground(Color.BLACK);
        this._connectOption.setLocX(48 - this._xPad);
        this._connectOption.setLocY(86 - this._yPad);
        this._connectOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onConnect();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._connectOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._connectOption.getSizeX() / SpriteAnim.this.getScale());
                SpriteAnim.this._select.setLocY(SpriteAnim.this._connectOption.getLocY() / SpriteAnim.this.getScale() + 1);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._hostNameMenu = new SpriteObj("", "", "", this._back, 184, 67, this.getScale());
        this._hostNameMenu.setIcon(icon);
        this._hostNameMenu.setLocX(0);
        this._hostNameMenu.setLocY(0);
        this._practiceOption = new SpriteObj("", "", "", this._mainInteract, 28, 18, this.getScale());
        this._practiceOption.setText("HP");
        this._practiceOption.setFont(this._bit);
        this._practiceOption.setForeground(Color.BLACK);
        this._practiceOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this.canInteract() && SpriteAnim.this._controller.getModel().getDigimon().getFullHealthPoints() < SpriteAnim.this._controller.getModel().getDigimon().getMaxHealth()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onPreTrain(Enum.Attribute.None);
                    SpriteAnim.this._gameButton.setAltIcon("tGameButton");
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._practiceOption.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._practiceOption.getSizeX() / SpriteAnim.this.getScale() - 6);
                SpriteAnim.this._select.setLocY(SpriteAnim.this._practiceOption.getLocY() / SpriteAnim.this.getScale() + 3);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._healthBar = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "healthBar.png", this._mainDisplay, 10, 60, this.getScale());
        this._healthBar.setLocX(95 - this._xPad);
        this._healthBar.setLocY(54 - this._yPad);
        this._healthUp = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "healthUp.png", this._mainDisplay, 17, 17, 1, this.getScale(), this.getScale() * 3);
        this._healthUp.setSize(51, 51);
        this._attackOption = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attackOptions.png", this._mainInteract, 30, 33, 1, this.getScale());
        this._attackOption.setLocX(39 - this._xPad);
        this._attackOption.setLocY(68 - this._yPad);
        this._attackOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._attackOption.setLoc(-100, -100);
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._animValue = 0;
                SpriteAnim.this._controller.onAttack();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._animValue = 5;
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._attackOption.drawNumMirror(0, false);
                SpriteAnim.this._attackOption.setVisible(true);
                SpriteAnim.this._animValue = 0;
            }
        });
        this._surrenderOption = new SpriteObj("", "", "", this._mainInteract, 30, 33, this.getScale());
        this._surrenderOption.setSpriteSheet(this._attackOption.getSpriteSheet());
        this._surrenderOption.setText("Surrender");
        this._surrenderOption.setFont(this._bit);
        this._surrenderOption.setForeground(Color.BLACK);
        this._surrenderOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 0;
                    SpriteAnim.this._controller.onSurrender();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._animValue = 7;
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Validation) {
                    SpriteAnim.this._surrenderOption.drawNumMirror(2, false);
                    SpriteAnim.this._surrenderOption.setVisible(true);
                }
                SpriteAnim.this._animValue = 0;
            }
        });
        this._yesLabel = new SpriteObj("", "", "", this._mainInteract, 44, 18, this.getScale());
        this._yesLabel.setText("Yes");
        this._yesLabel.setFont(this._bit);
        this._yesLabel.setForeground(Color.BLACK);
        this._yesLabel.setLocX(30 - this._xPad);
        this._yesLabel.setLocY(80 - this._yPad);
        this._yesLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.onYes()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._yesLabel.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._yesLabel.getSizeX() / SpriteAnim.this.getScale());
                SpriteAnim.this._select.setLocY(SpriteAnim.this._yesLabel.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._noLabel = new SpriteObj("", "", "", this._mainInteract, 26, 18, this.getScale());
        this._noLabel.setText("No");
        this._noLabel.setFont(this._bit);
        this._noLabel.setForeground(Color.BLACK);
        this._noLabel.setLocX(90 - this._xPad);
        this._noLabel.setLocY(80 - this._yPad);
        this._noLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onNo();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._select.setLocX(SpriteAnim.this._noLabel.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._noLabel.getSizeX() / SpriteAnim.this.getScale());
                SpriteAnim.this._select.setLocY(SpriteAnim.this._noLabel.getLocY() / SpriteAnim.this.getScale() + 2);
                SpriteAnim.this._select.setVisible(true);
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
            }
        });
        this._cardButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "card.png", this._mainInteract, 16, 26, 2, this.getScale());
        this._cardButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._error);
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._animValue = 5;
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._cardButton.setIcon(SpriteAnim.this._cardButton.getSpriteSheet()[SpriteAnim.this._cardButton.getSpriteNum()]);
                SpriteAnim.this._animValue = 0;
            }
        });
        this._firstBoss = new SpriteObj("", "", "", this._mainDisplay, 48, 48, this.getScale());
        this._secondBoss = new SpriteObj("", "", "", this._mainDisplay, 48, 48, this.getScale());
        this._thirdBoss = new SpriteObj("", "", "", this._mainDisplay, 48, 48, this.getScale());
        this._victoryMessage = new SpriteObj("", "", "", this._mainDisplay, 100, 100, this.getScale());
        this._victoryMessage.setFont(this._bit);
        this._victoryMessage.setForeground(Color.BLACK);
        this._victoryMessage.setLocX(43 - this._xPad);
        this._victoryMessage.setLocY(35 - this._yPad);
        this._victoryMessage.setText("<html><p style=\"text-align:center\">You saved<br>the Digital<br>World!</p></html>");
    }

    private void setVictoryMessageText(String s) {
        this._victoryMessage.setText("<html><p style=\"text-align:center\">" + s + "</p></html>");
    }

    private void initAttackButtons() {
        this._healthBarFull = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "healthBarFull.png", this._mainInteract, 10, 60, this.getScale());
        this._healthBarFull.setLocX(95 - this._xPad);
        this._healthBarFull.setLocY(54 - this._yPad);
        this._healthBarFull.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_HP && SpriteAnim.this._controller.getModel().getDigimon().getFullHealthPoints() < SpriteAnim.this._controller.getModel().getDigimon().getMaxHealth()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onHealthBar();
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_HP) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_HP) {
                    SpriteAnim.this._select.setLocX(SpriteAnim.this._healthBarFull.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._healthBarFull.getSizeX() / SpriteAnim.this.getScale() + 2);
                    SpriteAnim.this._select.setLocY(SpriteAnim.this._healthBarFull.getLocY() / SpriteAnim.this.getScale() + SpriteAnim.this._healthBarFull.getSizeY() / SpriteAnim.this.getScale() / 2 - SpriteAnim.this._select.getSizeY() / SpriteAnim.this.getScale() / 2);
                    SpriteAnim.this._select.setVisible(true);
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_HP) {
                    SpriteAnim.this._select.setLocX(-100);
                    SpriteAnim.this._select.setVisible(false);
                }
            }
        });
        this._vaccineAttack = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "red.png", this._mainInteract, 14, 14, this.getScale());
        this._vaccineAttack.setLocX(38 - this._xPad);
        this._vaccineAttack.setLocY(75 - this._yPad);
        this._vaccineAttack.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 0;
                    SpriteAnim.this._controller.onDescription(false);
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None) {
                    if (SpriteAnim.this._controller.getModel().getDigimon().getVaccinePower() > 0) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onVaccineAttack();
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 0;
                    SpriteAnim.this._controller.onDescription(true);
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select) {
                    if (SpriteAnim.this.canInteract()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onPreTrain(Enum.Attribute.Vaccine);
                        SpriteAnim.this._gameButton.setAltIcon("tGameButton");
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else if (SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._controller.onHPTrainingAttribute(Enum.Attribute.Vaccine);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks) {
                        SpriteAnim.this._select.setLocX(SpriteAnim.this._vaccineAttack.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._vaccineAttack.getSizeX() / SpriteAnim.this.getScale() + 4);
                        SpriteAnim.this._select.setLocY(SpriteAnim.this._vaccineAttack.getLocY() / SpriteAnim.this.getScale() + 2);
                        SpriteAnim.this._select.setVisible(true);
                    } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._currentAnim == Enum.State.HP_Training || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None) {
                        SpriteAnim.this.setBorder(SpriteAnim.this._vaccineAttack, 2, 2, 2, true);
                    }
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._currentAnim == Enum.State.HP_Training || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        this._dataAttack = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "green.png", this._mainInteract, 14, 14, this.getScale());
        this._dataAttack.setLocX(70 - this._xPad);
        this._dataAttack.setLocY(75 - this._yPad);
        this._dataAttack.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 1;
                    SpriteAnim.this._controller.onDescription(false);
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None) {
                    if (SpriteAnim.this._controller.getModel().getDigimon().getDataPower() > 0) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onDataAttack();
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 1;
                    SpriteAnim.this._controller.onDescription(true);
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select) {
                    if (SpriteAnim.this.canInteract()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onPreTrain(Enum.Attribute.Data);
                        SpriteAnim.this._gameButton.setAltIcon("tGameButton");
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else if (SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._controller.onHPTrainingAttribute(Enum.Attribute.Data);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks) {
                        SpriteAnim.this._select.setLocX(SpriteAnim.this._dataAttack.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._dataAttack.getSizeX() / SpriteAnim.this.getScale() + 4);
                        SpriteAnim.this._select.setLocY(SpriteAnim.this._dataAttack.getLocY() / SpriteAnim.this.getScale() + 2);
                        SpriteAnim.this._select.setVisible(true);
                    } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                        SpriteAnim.this.setBorder(SpriteAnim.this._dataAttack, 2, 2, 2, true);
                    }
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
        this._virusAttack = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "yellow.png", this._mainInteract, 14, 14, this.getScale());
        this._virusAttack.setLocX(100 - this._xPad);
        this._virusAttack.setLocY(75 - this._yPad);
        this._virusAttack.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 2;
                    SpriteAnim.this._controller.onDescription(false);
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None) {
                    if (SpriteAnim.this._controller.getModel().getDigimon().getVirusPower() > 0) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onVirusAttack();
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._animValue = 2;
                    SpriteAnim.this._controller.onDescription(true);
                } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select) {
                    if (SpriteAnim.this.canInteract()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onPreTrain(Enum.Attribute.Virus);
                        SpriteAnim.this._gameButton.setAltIcon("tGameButton");
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                } else if (SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._controller.onHPTrainingAttribute(Enum.Attribute.Virus);
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.AttackType_Validation || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Training_Select || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Enemy_Attacks) {
                        SpriteAnim.this._select.setLocX(SpriteAnim.this._virusAttack.getLocX() / SpriteAnim.this.getScale() + SpriteAnim.this._virusAttack.getSizeX() / SpriteAnim.this.getScale() + 4);
                        SpriteAnim.this._select.setLocY(SpriteAnim.this._virusAttack.getLocY() / SpriteAnim.this.getScale() + 2);
                        SpriteAnim.this._select.setVisible(true);
                    } else if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                        SpriteAnim.this.setBorder(SpriteAnim.this._virusAttack, 2, 2, 2, true);
                    }
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._select.setLocX(-100);
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Data_Power || SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && SpriteAnim.this._controller.getBattle() != null && SpriteAnim.this._controller.getBattle().getBattleType() != Battle.BattleType.None || SpriteAnim.this._currentAnim == Enum.State.HP_Training) {
                    SpriteAnim.this._border.setVisible(false);
                }
            }
        });
    }

    private void initSaveMenu() {
        this._saveOption = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "save.png", this._mainInteract, 9, 9, 2, (byte)(this.getScale() * 3));
        this._saveOption.setLocX(5);
        this._saveOption.setLocY(6);
        this._saveOption.setSizeX(10);
        this._saveOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._saveOption.setVisible(false);
                SpriteAnim.this._controller.onSave();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation) {
                    SpriteAnim.this._saveOption.drawNumMirror(1, false);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation) {
                    SpriteAnim.this._saveOption.drawNumMirror(0, false);
                }
            }
        });
        this._quitOption = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "exit.png", this._mainInteract, 9, 16, 2, (byte)(this.getScale() * 3));
        this._quitOption.setLocX(21);
        this._quitOption.setLocY(3.7);
        this._quitOption.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onQuit();
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._quitOption.drawNumMirror(0, false);
                    SpriteAnim.this._quitOption.setVisible(true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu() == Enum.Menu.Save_Validation) {
                    SpriteAnim.this._quitOption.drawNumMirror(2, false);
                    SpriteAnim.this._quitOption.setVisible(true);
                }
            }
        });
        this._backButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "backButton.png", this._mainInteract, 15, 15, this.getScale());
        this._backButton.setLocX(26 - this._xPad);
        this._backButton.setLocY(53 - this._yPad);
        this._backButton.addAltSprite(ViewUtil.getTransparentImage(this._backButton.getAltSprite("backButton"), 0.25f), "backButtonTransp");
        this._backButton.setAltIcon("backButtonTransp");
        this._backButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onBack();
                    SpriteAnim.this._backButton.setAltIcon("backButtonTransp");
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._backButton.setAltIcon("backButton");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._backButton.setAltIcon("backButtonTransp");
                }
            }
        });
        this._pauseButton = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "pause.png", this._mainInteract, 13, 14, this.getScale());
        this._pauseButton.addAltSprite(ViewUtil.getTransparentImage(this._pauseButton.getAltSprite("pause"), 0.5f), "tPause");
        this._pauseButton.setLocX(87);
        this._pauseButton.setLocY(42);
        this._pauseButton.setAltIcon("tPause");
        this._pauseButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.onPause()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._select);
                SpriteAnim.this._pauseButton.setAltIcon("pause");
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._pauseButton.setAltIcon("tPause");
            }
        });
    }

    private void setItemSet() {
        ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, "Items", this._itemType, this._itemLabel, 1, 16, 16, this.getScale() * 3);
    }

    private void setFoodSet() {
        this.setFoodSet(this._foodType);
    }

    private void setFoodSet(Consumable c) {
        ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, "Food", c, this._foodLabel, 6, 24, 24, this.getScale());
    }

    private SpriteObj getOppSet(Enum.Stage info, int spriteSet, int spriteNum) {
        String spriteName = "sprites" + (Object)((Object)info) + spriteSet + ".png";
        SpriteObj obj = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, spriteName, null, 48, 48, this.getScale());
        obj.setSpriteSheet(ViewUtil.divideIntoColumn(obj.getSpriteLoc(), info == Enum.Stage.Egg ? 6 : 12, spriteNum, 48, 48, this.getScale()));
        return obj;
    }

    private SpriteObj getOppSet(Enum.Stage info, int spriteSet, int spriteNum, boolean saveMirror) {
        SpriteObj obj = this.getOppSet(info, spriteSet, spriteNum);
        if (saveMirror) {
            obj.saveSpriteMirror();
        }
        return obj;
    }

    private Icon getIndividualIcon(Enum.Stage info, int spriteSet, double scale, int spriteNum, int row, int width, int height, int emptyPixels) {
        String spriteName = "sprites" + (Object)((Object)info) + spriteSet + ".png";
        return ViewUtil.getIndividualIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, spriteName, scale, spriteNum, row, width, height, emptyPixels);
    }

    private void addCharacterListener(SpriteObj obj, final PhysicalState digimon) {
        obj.addMouseListener(new MouseAdapter(this){
            final /* synthetic */ SpriteAnim this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void mousePressed(MouseEvent e) {
                if (this.this$0._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    this.this$0._sounds.playSound(SoundConfig._click);
                    this.this$0._controller.onDifficulty(0);
                } else {
                    this.this$0.characterButton();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (this.this$0._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    this.this$0._sounds.playSound(SoundConfig._select);
                    this.this$0.setBorder(this.this$0._character, 5, 5, 3, true);
                } else if (this.this$0._currentAnim == Enum.State.Idling || Utility.containsState(Utility.ENABLE_DURING_STATE, this.this$0._currentAnim)) {
                    this.this$0._sounds.playSound(SoundConfig._select);
                    this.this$0.selectCharacter(digimon);
                } else {
                    this.this$0._select.setAltIcon("select");
                    this.this$0._select.setVisible(false);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (this.this$0._controller.getCurrentMenu() == Enum.Menu.SetDifficulty) {
                    this.this$0._border.setVisible(false);
                } else {
                    this.this$0._select.setLocX(-100);
                    this.this$0._select.setAltIcon("select");
                    this.this$0._select.setVisible(false);
                }
            }
        });
    }

    private void selectCharacter(PhysicalState digimon) {
        int mirrorLoc = (!digimon.isFuton() ? this._character.getLocX() / this.getScale() : this._itemLabel.getLocX() / this.getScale()) - 12;
        int loc = (!digimon.isFuton() ? this._character.getLocX() / this.getScale() + this._character.getSizeX() / this.getScale() : this._itemLabel.getLocX() / this.getScale() + this._itemLabel.getSizeX() / this.getScale()) + 6;
        if (this._character.getIsMirror() && loc > this._mainDisplay.getWidth() || mirrorLoc > 0) {
            this._select.setLocX(mirrorLoc);
            this._select.setAltIcon("selectMirror");
        } else {
            this._select.setLocX(loc);
            this._select.setAltIcon("select");
        }
        this._select.setLocY(this._character.getLocY() / this.getScale() + this._character.getSizeY() / this.getScale() / 2 - this._select.getSizeY() / this.getScale() / 2);
        this._select.setVisible(true);
    }

    private void initMapMenu() {
        this._map = new SpriteObj("", "", "", this._mainDisplay, this.MAP_SIZE.x, this.MAP_SIZE.y, this.getScale());
        this._map.addMouseListener(new MouseAdapter(){
            PhysicalState digimon;
            {
                this.digimon = SpriteAnim.this._controller.getModel().getDigimon();
            }

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu().equals((Object)Enum.Menu.WorldMapSelect) || SpriteAnim.this._controller.getCurrentMenu().equals((Object)Enum.Menu.WorldMapSelect_Ticket) && this.digimon.getWorld().getUnlockedMaps()[SpriteAnim.this._consumablePage].getIsUnlocked()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onMapSelect();
                } else if (SpriteAnim.this._controller.getCurrentMenu().equals((Object)Enum.Menu.WorldMapSelect)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (SpriteAnim.this._controller.getCurrentMenu().equals((Object)Enum.Menu.WorldMapSelect) || SpriteAnim.this._controller.getCurrentMenu().equals((Object)Enum.Menu.WorldMapSelect_Ticket) && this.digimon.getWorld().getUnlockedMaps()[SpriteAnim.this._consumablePage].getIsUnlocked()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.setBorder(SpriteAnim.this._map, 3, 3, 2, true);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                SpriteAnim.this._border.setVisible(false);
            }
        });
        this._okValidation = new SpriteObj("", "", "", this._mainDisplay, 34, 18, this.getScale());
        this._okValidation.setText("OK?");
        this._okValidation.setFont(this._bit);
        this._okValidation.setForeground(Color.BLACK);
        this._stepsLabel = new SpriteObj("", "", "", this._mainDisplay, 50, 18, this.getScale());
        this._stepsLabel.setText("Steps");
        this._stepsLabel.setFont(this._bit);
        this._stepsLabel.setForeground(Color.BLACK);
        this._stepsPanel = new SpriteObj("", "", "", this._mainDisplay, 175, 50, this.getScale());
        this._stepsPanel.setBorder(null);
        this._stepsPanel.setFont(this._bit);
        this._stepsPanel.setForeground(Color.BLACK);
        this._travelLabel = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "stopped.png", this._mainInteract, 26, 22, this.getScale());
        this._travelLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "walking.png");
        this._travelLabel.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "running.png");
        this._travelLabel.addAltSprite(ViewUtil.getTransparentImage(this._travelLabel.getAltSprite("stopped"), 0.25f), "tStopped");
        this._travelLabel.addAltSprite(ViewUtil.getTransparentImage(this._travelLabel.getAltSprite("walking"), 0.25f), "tWalking");
        this._travelLabel.addAltSprite(ViewUtil.getTransparentImage(this._travelLabel.getAltSprite("running"), 0.25f), "tRunning");
        this._travelLabel.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                if (!digimon.getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this.changeTravelSpeed();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this.checkTravelLabel(SpriteAnim.this._controller.getModel().getDigimon().getWorld(), false);
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this.checkTravelLabel(SpriteAnim.this._controller.getModel().getDigimon().getWorld(), true);
                }
            }
        });
        this._zoneDetail = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "travelMenu.png", this._mainDisplay, 99, 26, this.getScale());
        this._townLabel = new SpriteObj("", "", "", this._mainDisplay, 100, 32, this.getScale());
        this._chooseMaps = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "changeMaps.png", this._mainInteract, 22, 17, this.getScale());
        this._chooseMaps.addAltSprite(ViewUtil.getTransparentImage(this._chooseMaps.getAltSprite("changeMaps"), 0.25f), "tChangeMaps");
        this._chooseMaps.setLoc(28 - this._xPad, 71 - this._yPad);
        this._chooseMaps.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onMapChange();
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._chooseMaps.setAltIcon("changeMaps");
                }
            }

            @Override
            public void mouseExited(MouseEvent e) {
                if (!SpriteAnim.this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                    SpriteAnim.this._chooseMaps.setAltIcon("tChangeMaps");
                }
            }
        });
    }

    public void setupZones() {
        this._zoneButtons.clear();
        MapLevel map = this._controller.getModel().getDigimon().getWorld().getCurrentMap();
        if (map != null) {
            this._map.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "" + map.getImage());
            for (final Zone zone : map.getZones()) {
                if (zone == null) continue;
                int[] p = zone.getLoc();
                final SpriteObj zoneButton = new SpriteObj("", "", "", this._mainInteract, 9, 9, this.getScale());
                this._zoneButtons.add(zoneButton);
                zoneButton.addAltSprite(this.MOD_FOLDER, this.RESOURCES_FOLDER, "zoneComplete.png");
                zoneButton.setLoc(p[0] + this.MAP_LOC.x, p[1] + this.MAP_LOC.y);
                zoneButton.setVisible(false);
                zoneButton.addMouseListener(new MouseAdapter(this){
                    final /* synthetic */ SpriteAnim this$0;
                    {
                        this.this$0 = this$0;
                    }

                    @Override
                    public void mousePressed(MouseEvent e) {
                        if (!(this.this$0._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange) || this.this$0._controller.getCurrentMenu() != Enum.Menu.MapZoneSelect && this.this$0._controller.getCurrentMenu() != Enum.Menu.ChooseZone)) {
                            boolean valid = false;
                            switch (this.this$0._controller.getCurrentMenu()) {
                                case ChooseZone: {
                                    valid = !zone.getIsCurrent() && (zone.getIsComplete() || zone.getIsUnlocked());
                                    break;
                                }
                                case MapZoneSelect: {
                                    boolean bl = valid = zone.getIsCurrent() || zone.getIsUnlocked() || zone.getIsComplete();
                                }
                            }
                            if (valid) {
                                this.this$0._selectZone = zone;
                                this.this$0._controller.onZone(zone.getIsCurrent());
                                this.this$0._sounds.playSound(SoundConfig._click);
                            } else {
                                this.this$0._sounds.playSound(SoundConfig._error);
                            }
                        }
                    }

                    @Override
                    public void mouseEntered(MouseEvent e) {
                        if (!this.this$0._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                            this.this$0._sounds.playSound(SoundConfig._select);
                            this.this$0.setBorder(zoneButton, 3, 3, 2, true);
                        }
                    }

                    @Override
                    public void mouseExited(MouseEvent e) {
                        if (!this.this$0._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                            this.this$0._border.setVisible(false);
                        }
                    }
                });
            }
        }
    }

    private void changeTravelSpeed() {
        WorldMap world = this._controller.onTravel();
        this.setSpriteCharDefault();
        this.checkTravelLabel(world, false);
    }

    private void checkTravelLabel(WorldMap world, boolean t) {
        byte speed = world.getTravelSpeed();
        switch (speed) {
            case 0: {
                this._travelLabel.setAltIcon(t ? "tStopped" : "stopped");
                break;
            }
            case 1: {
                this._travelLabel.setAltIcon(t ? "tWalking" : "walking");
                break;
            }
            case 2: {
                this._travelLabel.setAltIcon(t ? "tRunning" : "running");
            }
        }
        if (world.getTravelRight()) {
            this._travelLabel.setIcon(ViewUtil.flipIcon(this._travelLabel.getIcon()));
        }
    }

    private void initCardsMenu() {
    }

    private void characterButton() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (this._controller.getCurrentMenu() == Enum.Menu.None && (digimon.getCurrentState() == Enum.State.Idling || digimon.getCurrentState() == Enum.State.Dying || digimon.getCurrentState() == Enum.State.GiftCall || digimon.getCurrentState() == Enum.State.DiscoverCall || digimon.getCurrentState() == Enum.State.RequestCall || digimon.getCurrentState() == Enum.State.TournamentAlert || Utility.containsState(Utility.ENABLE_DURING_STATE, digimon.getCurrentState())) && (this._currentAnim == Enum.State.Idling || this._currentAnim == Enum.State.Dying || this._currentAnim == Enum.State.GiftCall || this._currentAnim == Enum.State.DiscoverCall || this._currentAnim == Enum.State.RequestCall || this._currentAnim == Enum.State.TournamentAlert || Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentAnim))) {
            this._controller.onCharacter();
            if (this._currentAnim != Enum.State.Dying) {
                this._sounds.playSound(SoundConfig._click);
            }
        }
    }

    private void addMainMenuListeners() {
        this._menuButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                SpriteAnim.this._controller.onMenu(e);
                SpriteAnim.this._frame = 0;
            }
        });
        this._statusButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._statusButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onStatus(e);
                    SpriteAnim.this._statusButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._statusButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._statusButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._statusButton.getIsEnabled()) {
                    SpriteAnim.this._statusButton.setAltIcon(0);
                }
            }
        });
        this._feedButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._feedButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onFeedMenu();
                    SpriteAnim.this._feedButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._feedButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._feedButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._feedButton.getIsEnabled()) {
                    SpriteAnim.this._feedButton.setAltIcon(0);
                }
            }
        });
        this._digisoulButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._digisoulButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onDigisoul();
                    SpriteAnim.this._digisoulButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._digisoulButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._digisoulButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._digisoulButton.getIsEnabled()) {
                    SpriteAnim.this._digisoulButton.setAltIcon(0);
                }
            }
        });
        this._gameButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._gameButton.getIsEnabled()) {
                    if (SpriteAnim.this.canInteract()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onGameButton();
                        SpriteAnim.this.disposeMusic();
                        SpriteAnim.this._gameButton.setAltIcon(0);
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._gameButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._gameButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._gameButton.getIsEnabled()) {
                    SpriteAnim.this._gameButton.setAltIcon(0);
                }
            }
        });
        this._battleButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                if (SpriteAnim.this._battleButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onBattle();
                    SpriteAnim.this._battleButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._battleButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._battleButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._battleButton.getIsEnabled()) {
                    SpriteAnim.this._battleButton.setAltIcon(0);
                }
            }
        });
        this._washButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._washButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onClean();
                    SpriteAnim.this._washButton.setAltIcon(0);
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._washButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._washButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._washButton.getIsEnabled()) {
                    SpriteAnim.this._washButton.setAltIcon(0);
                }
            }
        });
        this._lightButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._lightButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onLights();
                    SpriteAnim.this._lightButton.setAltIcon(0);
                    if (SpriteAnim.this._controller.getModel().getDigimon().getAsleep()) {
                        SpriteAnim.this._frame = 0;
                    }
                } else {
                    SpriteAnim.this._sounds.playSound(SoundConfig._error);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._lightButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._lightButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._lightButton.getIsEnabled()) {
                    SpriteAnim.this._lightButton.setAltIcon(0);
                }
            }
        });
        this._firstAidButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._firstAidButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onFirstAid();
                    SpriteAnim.this._firstAidButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._firstAidButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._firstAidButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._firstAidButton.getIsEnabled()) {
                    SpriteAnim.this._firstAidButton.setAltIcon(0);
                }
            }
        });
        this._tempButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._tempButton.getIsEnabled()) {
                    SpriteAnim.this._controller.onSeason();
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._tempButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._tempButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._tempButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._tempButton.getIsEnabled()) {
                    SpriteAnim.this._tempButton.setAltIcon(0);
                }
            }
        });
        this._evolutionTreeButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._evolutionTreeButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onEvolButton();
                    SpriteAnim.this._evolutionTreeButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._evolutionTreeButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._evolutionTreeButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._evolutionTreeButton.getIsEnabled()) {
                    SpriteAnim.this._evolutionTreeButton.setAltIcon(0);
                }
            }
        });
        this._mapButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._mapButton.getIsEnabled()) {
                    Enum.Stage digimon = SpriteAnim.this._controller.getModel().getDigimon().getGrowthStage();
                    if (!SpriteAnim.this._controller.getModel().getDigimon().getTournament().getActive() && SpriteAnim.this.canInteract()) {
                        SpriteAnim.this._sounds.playSound(SoundConfig._click);
                        SpriteAnim.this._controller.onMapButton();
                        SpriteAnim.this._mapButton.setAltIcon(0);
                    } else {
                        SpriteAnim.this._sounds.playSound(SoundConfig._error);
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._mapButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._mapButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._mapButton.getIsEnabled()) {
                    SpriteAnim.this._mapButton.setAltIcon(0);
                }
            }
        });
        this._clockButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._clockButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onClockButton();
                    SpriteAnim.this._clockButton.setAltIcon(0);
                    SpriteAnim.this.checkPlayPausedLabel();
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._clockButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    if (!SpriteAnim.this._controller.isPlaying()) {
                        SpriteAnim.this.checkPlayPausedLabel();
                    } else {
                        SpriteAnim.this._clockButton.setAltIcon(1);
                    }
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._clockButton.getIsEnabled()) {
                    SpriteAnim.this._clockButton.setAltIcon(0);
                }
            }
        });
        this._settingsButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._settingsButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._controller.onSettingsButton();
                    SpriteAnim.this._settingsButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._settingsButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._settingsButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._settingsButton.getIsEnabled()) {
                    SpriteAnim.this._settingsButton.setAltIcon(0);
                }
            }
        });
        this._saveButton.addMouseListener(new MouseAdapter(){

            @Override
            public void mousePressed(MouseEvent e) {
                if (SpriteAnim.this._saveButton.getIsEnabled()) {
                    SpriteAnim.this._controller.onSaveButton();
                    SpriteAnim.this._sounds.playSound(SoundConfig._click);
                    SpriteAnim.this._saveButton.setAltIcon(0);
                }
            }

            @Override
            public void mouseEntered(MouseEvent evt) {
                if (SpriteAnim.this._saveButton.getIsEnabled()) {
                    SpriteAnim.this._sounds.playSound(SoundConfig._select);
                    SpriteAnim.this._saveButton.setAltIcon(1);
                }
            }

            @Override
            public void mouseExited(MouseEvent evt) {
                if (SpriteAnim.this._saveButton.getIsEnabled()) {
                    SpriteAnim.this._saveButton.setAltIcon(0);
                }
            }
        });
    }

    private void checkPlayPausedLabel() {
        if (!this._controller.isPlaying()) {
            this._clockButton.setAltIcon(2);
        } else {
            this._clockButton.setAltIcon(1);
        }
    }

    private Enum.Attribute checkTrainingAttribute() {
        Enum.Attribute attribute = Enum.Attribute.None;
        int spriteNum = this._attackSprite.getSpriteNum();
        attribute = spriteNum >= 0 && spriteNum < 25 ? Enum.Attribute.Vaccine : (spriteNum >= 50 ? Enum.Attribute.Virus : Enum.Attribute.Data);
        return attribute;
    }

    public void AddListener(ClockTic controller, PhysicalState digimon) {
        this._controller = controller;
        this._interval = (byte)(this._controller.getTargetFPS() / 10);
        this.initComponents(digimon);
    }

    public void resetScreenExceptMenuRect() {
        this.resetScreenExcept(this._menuRect);
    }

    private synchronized void resetScreenExcept(Component e) {
        for (Component c : this._display.getComponents()) {
            if (c == this._mainDisplay || c == e) continue;
            c.setVisible(false);
        }
        for (Component c : this._mainDisplay.getComponents()) {
            if (c == e) continue;
            c.setVisible(false);
        }
        for (Component c : this._interact.getComponents()) {
            if (c == this._mainInteract || c == this._menuInteract || c == e) continue;
            c.setVisible(false);
        }
        for (Component c : this._mainInteract.getComponents()) {
            if (c == e) continue;
            c.setVisible(false);
        }
        this.validate();
        this.repaint();
    }

    public void resetScreen() {
        this.resetScreenExcept(null);
    }

    private void resetBack() {
        for (Component c : this._back.getComponents()) {
            c.setVisible(false);
        }
    }

    public void updateDebug(PhysicalState digimon) {
        if (this._debugFrame != null && this._debugText1 != null && this._debugText2 != null) {
            digimon.writeVars(this._debugText1, this._debugText2, this._controller.getCurrentMenu());
        }
    }

    public void checkSystemMenus(Enum.Menu currentMenu, Enum.Menu lastMenu, PhysicalState digimon, ViewSettings settings) {
        digimon.setCanEvolveOrDie(false);
        if (this._keyboard != null) {
            this._keyboard.setCursorPosition(-1);
        }
        this._menuRect.setVisible(!ViewUtil.containsMenu(ViewUtil.REMOVE_HIGHLIGHT, currentMenu));
        if (currentMenu != null && currentMenu != Enum.Menu.None) {
            this._currentAnim = digimon.getCurrentState();
        } else if (currentMenu == null) {
            currentMenu = Enum.Menu.None;
        }
        this._frame = -1 * this._interval;
        if (currentMenu != Enum.Menu.None) {
            this.disableMainMenu();
        }
        switch (currentMenu) {
            case Loading: {
                this.drawLoading();
                break;
            }
            case Start: {
                this.drawStartMenu();
                break;
            }
            case Set_EggClock: {
                this.drawNewGameMenu();
                break;
            }
            case SetDifficulty: {
                this.drawSetDifficultyMenu();
                break;
            }
            case Save_Name: {
                this.drawSaveLoadMenu("SAVE");
                break;
            }
            case Load_Name: {
                this.drawSaveLoadMenu("LOAD");
                break;
            }
            case Restart: {
                this.drawRestartMenu();
                break;
            }
            case Choose_Egg: {
                this.drawEggMenu();
                break;
            }
            case SaveExit_Validation: {
                this.drawSaveExitValidation();
                break;
            }
            case Save_Validation: {
                this.drawSaveMenu(digimon);
                break;
            }
            case DigiMemory_Validation: {
                this.drawDigimemoryValidation();
                break;
            }
            case EvolutionMenu: {
                this.drawEvolutionMenu();
                break;
            }
            case EvolutionInventory: {
                this.drawEvolutionInventory();
                break;
            }
            case EvolutionState: {
                this.drawEvolutionState(digimon);
                break;
            }
            case EvolSilhouette: {
                this.drawEvolSilhouette();
                break;
            }
            case DNA_Validation: {
                this.drawDNAMenu();
                break;
            }
            case DNA_Stats: {
                this.drawDNAStats();
                break;
            }
            case DNA_Detail: {
                this.drawDNADetail(Enum.Field.values()[this._consumablePage]);
                break;
            }
            case DNA_Inventory: {
                this.drawDNACharge();
                break;
            }
            case DNA_GenerateValidate: {
                this.drawDNAGenerateValidate();
                break;
            }
            case Battle_Validation: {
                this.drawBattleMenu();
                break;
            }
            case Battle_Style: {
                this.drawBattleStyleMenu();
                break;
            }
            case Tourney_Options: {
                this.drawTourneyMenu();
                break;
            }
            case Season_Records: {
                this.drawRecordsSelectMenu();
                break;
            }
            case Spring_Records: {
                this.drawRecordsMenu(Enum.Season.Spring);
                break;
            }
            case Summer_Records: {
                this.drawRecordsMenu(Enum.Season.Summer);
                break;
            }
            case Fall_Records: {
                this.drawRecordsMenu(Enum.Season.Fall);
                break;
            }
            case Winter_Records: {
                this.drawRecordsMenu(Enum.Season.Winter);
                break;
            }
            case Registration_Prelim_Details: 
            case Records_Prelim_Details: {
                this.drawTrophyPrelimDetails();
                break;
            }
            case TrophyDetails: {
                this.drawTrophyDetailsMenu(true);
                break;
            }
            case TrophyPrizeBits: {
                this.drawTrophyPrizeBits(digimon);
                break;
            }
            case TrophyPrizeItem: {
                this.drawTrophyPrizeItem();
                break;
            }
            case Tourney_Enter: {
                this.drawTourneySchedule();
                break;
            }
            case Tourney_Registration: {
                this.drawTourneyRegistration();
                break;
            }
            case Tourney_Validation: {
                this.drawTourneyValidation();
                break;
            }
            case Roster: {
                this.drawRoster();
                break;
            }
            case Royale_Lineup: {
                this.drawRoyaleLineup();
                break;
            }
            case Tourney_Surrender: {
                this.drawTourneySurrender();
                break;
            }
            case Card_Options: {
                this.drawCardMenu();
                break;
            }
            case Card_Shop: {
                this.drawCardShop();
                break;
            }
            case Multi_Validation_Battle: 
            case Multi_Validation_Jogress: {
                this.drawMultiValidation();
                break;
            }
            case Host_Name_Jogress: 
            case Host_Name_Battle: {
                this.drawHostNameMenu("HOST", "127.0.0.1");
                break;
            }
            case Host_Port_Battle: 
            case Host_Port_Jogress: {
                this.drawHostNameMenu("PORT", Config._portNum + "");
                break;
            }
            case Jogress_Mismatch: {
                this.drawJogressMismatch();
                break;
            }
            case ConnectError_Battle: 
            case ConnectError_Jogress: {
                this.drawConnectError();
                break;
            }
            case Battle_VS: {
                this.drawVSMenu();
                break;
            }
            case Attack_Validation: {
                this.drawAttackMenu();
                break;
            }
            case AttackType_Validation: {
                this.drawAttackTypeMenu();
                break;
            }
            case Attack_Description: {
                this.drawAttackDescription();
                break;
            }
            case EnemyAttack_Description: {
                this.drawEnemyAttackDescription();
                break;
            }
            case Enemy_Attacks: {
                this.drawEnemyAttacks();
                break;
            }
            case UseCard_Validation: {
                break;
            }
            case Clock_Validation: {
                this.drawClockValidation();
                break;
            }
            case Surrender_Validation: {
                this.drawSurrenderMenu();
                break;
            }
            case Investigate_Validation: {
                this.drawInvestigateMenu();
                break;
            }
            case Feed_Validation: {
                this.drawFeedMenu();
                break;
            }
            case Food_Buy_Sell_Validation: 
            case Item_Buy_Sell_Validation: {
                this.drawBuySellValidation();
                break;
            }
            case Food_Inventory: {
                this.drawFoodInventory();
                break;
            }
            case Food_Inventory_Sell: {
                this.drawFoodSaleInventory();
                break;
            }
            case Food_Shop: {
                this.drawFoodShop();
                break;
            }
            case Sell_Food: {
                this.drawSellFood();
                break;
            }
            case Buy_Food: {
                this.drawBuyFood();
                break;
            }
            case Food_Purchase: {
                this.drawFoodPurchase(this._consumableType.getPurchasePrice());
                break;
            }
            case Food_Sale: {
                this.drawFoodSale(this._consumableType.getResellPrice());
                break;
            }
            case Item_Purchase: {
                this.drawItemPurchase(this._consumableType.getPurchasePrice());
                break;
            }
            case Item_Sale: {
                this.drawItemSale(this._consumableType.getResellPrice());
                break;
            }
            case Habitat_Purchase: {
                this.drawHabitatPurchase(digimon.getHabitats().get(this._habitat).getPrice());
                break;
            }
            case Use_Food: 
            case Use_Med_Food: {
                this.drawUseFood();
                break;
            }
            case PraiseScold_Validation: {
                this.drawPraiseMenu();
                break;
            }
            case Medical: {
                this.drawMedical();
                break;
            }
            case Training_Select: {
                this.drawTrainingSelect();
                break;
            }
            case Data_Calories: {
                this.drawDataCalories(digimon);
                break;
            }
            case Food_Calories: {
                this.drawFoodCalories(this._foodType.getCalories(), digimon);
                break;
            }
            case Data_Clock: {
                this.drawDataClock();
                break;
            }
            case Data_Temp: {
                this.drawDataTemp();
                break;
            }
            case Data_Status: {
                this.drawDataStatus();
                break;
            }
            case Data_Power: {
                this.drawDataPower();
                break;
            }
            case Data_HP: {
                this._frame = 0;
                this.drawDataHP(digimon.getHealthPoints(), digimon.getFullHealthPoints());
                break;
            }
            case Data_Person: {
                this.drawDataPerson();
                break;
            }
            case Data_Person_Detail: {
                this.drawDataPersonDetail(digimon);
                break;
            }
            case Data_Likes: {
                this.drawDataFavorites(digimon.getTimeRanks().getUnlockedFav() ? digimon.getFavTime() : null, digimon.getFoodRanks().getUnlockedFav() ? digimon.getFavFood() : null, digimon.getAttributeRanks().getUnlockedFav() ? digimon.getFavAtt() : null, "Favorite");
                break;
            }
            case Data_Dislikes: {
                this.drawDataFavorites(digimon.getTimeRanks().getUnlockedDislike() ? digimon.getDislikedTime() : null, digimon.getFoodRanks().getUnlockedDislike() ? digimon.getDislikedFood() : null, digimon.getAttributeRanks().getUnlockedDislike() ? digimon.getDislikedAtt() : null, "Disliked");
                break;
            }
            case Data_SpeciesLikes: {
                this.drawDataFavorites(digimon.getTimePreference(), digimon.getFoodPreference(), digimon.getAttributePreference(), "Inclined");
                break;
            }
            case Data_SpeciesDislikes: {
                this.drawDataFavorites(digimon.getTimeAversion(), digimon.getFoodAversion(), digimon.getAttributeAversion(), "Averse");
                break;
            }
            case Data_Intolerant: {
                this.drawDataIntolerant(digimon.getFoodIntolerance().get(0));
                break;
            }
            case Data_Strength: {
                this.drawDataHealth(false);
                break;
            }
            case Data_Hunger: {
                this.drawDataHealth(true);
                break;
            }
            case Data_Nutrition: {
                this.drawDataNutrition(digimon.getProtein(), digimon.getMineral(), digimon.getVitamin());
                break;
            }
            case Buy_Nutrition: 
            case Use_Nutrition: 
            case Med_Nutrition: 
            case Sell_Nutrition: {
                this.drawFoodNutrition(this._foodType.getProtein(), this._foodType.getMineral(), this._foodType.getVitamin(), this._foodType.getTotalNutrition());
                break;
            }
            case Data_HealthTrack: {
                this.drawDataHealthTrack();
                break;
            }
            case Data_Energy: {
                this.drawDataEnergy();
                break;
            }
            case Data_Battles: {
                this.drawDataBattles();
                break;
            }
            case Data_BattleLevels: {
                this.drawDataBattleLevels();
                break;
            }
            case Set_Clock: {
                this.drawSetClockMenu(digimon.getTimeSkip());
                break;
            }
            case Set_AutoCare: {
                this.drawAutoCareValidation();
                break;
            }
            case WorldMapSelect: {
                this.drawMapSelect(true);
                break;
            }
            case WorldMapSelect_Ticket: {
                this.drawMapSelect(false);
                break;
            }
            case MapZoneSelect: {
                this.drawZoneSelect(true);
                break;
            }
            case Map_Validation: 
            case Map_Validation_Ticket: {
                this.drawMapValidation();
                break;
            }
            case Steps: {
                this.drawSteps();
                break;
            }
            case Zone_Validation: 
            case Zone_Validation_Ticket: {
                this.drawZoneValidation();
                break;
            }
            case ChooseZone: {
                this.drawZoneSelect(false);
                break;
            }
            case ZoneDetail: {
                this.drawZoneDetail();
                break;
            }
            case Settings: {
                this.drawSettingsMenu(settings);
                break;
            }
            case Shop_Validation: {
                this.drawShopValidation();
                break;
            }
            case Inventory_Validation: {
                this.drawInventoryValidation();
                break;
            }
            case Item_Inventory: {
                this.drawItemInventory();
                break;
            }
            case Item_Inventory_Sell: {
                this.drawItemSaleInventory();
                break;
            }
            case Item_Shop: {
                this.drawItemShop();
                break;
            }
            case Use_Med_Item: 
            case Use_Item: 
            case UseEvolutionItem: {
                this.drawUseItem();
                break;
            }
            case Sell_Item: {
                this.drawSellItem();
                break;
            }
            case Buy_Item: {
                this.drawBuyItem();
                break;
            }
            case Habitat_Shop: {
                this.drawHabitatShop(currentMenu, lastMenu);
                break;
            }
            case Habitat_Inventory: {
                this.drawHabitatInventory(lastMenu);
                break;
            }
            case Habitat_Description: {
                this.drawHabitatDescription(false);
                break;
            }
            case Habitat_Compatibility: 
            case Habitat_Shop_Compatibility: {
                this.drawHabitatCompatibility(currentMenu);
                break;
            }
            case Habitat_Incompatibility: 
            case Habitat_Shop_Incompatibility: {
                this.drawHabitatCompatibility(currentMenu);
                break;
            }
            case Habitat_Shop_Description: {
                this.drawHabitatDescription(true);
                break;
            }
            case EvolutionTree: {
                break;
            }
            default: {
                this._frame = -1 * this._interval;
                this.drawMainMenu();
            }
        }
    }

    private void drawLoading() {
        try {
            this._back.setVisible(true);
            this._shell.setVisible(true);
            this._background.setVisible(true);
            this._mainBackground.setVisible(true);
            this._roomEffect.setVisible(true);
            this._roomEffect.setAltIcon("loading");
            this._roomEffect.setVisible(true);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void drawStartMenu() {
        this.resetBack();
        int x = this._startMenu.getSizeX();
        int y = this._startMenu.getSizeY();
        Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
        this.setLocation(dim.width / 2 - x / 2, dim.height / 2 - y / 2);
        this._display.setSize(x, y);
        this._mainDisplay.setSize(x, y);
        this._interact.setSize(x, y);
        this._mainInteract.setSize(x, y);
        this._menuInteract.setSize(x, y);
        this._closeButton.setLocX(148);
        this._closeButton.setLocY(1);
        this._closeButton.setVisible(true);
        this._startButton.setVisible(true);
        this._loadButton.setVisible(true);
        this._startMenu.setVisible(true);
        this._back.setSize(x, y);
        this._back.setLocation(0, 0);
        this.setSize(x, y);
        if (this._controller.getCurrentMenu() == Enum.Menu.Start && this._longClip == null) {
            Calendar currentDate = Calendar.getInstance();
            int hour = currentDate.get(11);
            this._longClip = hour >= 8 && hour < 20 ? this._sounds.loopSound(SoundConfig._startMenuDayLoop, SoundConfig._musicVolume) : this._sounds.loopSound(SoundConfig._startMenuNightLoop, SoundConfig._musicVolume);
        }
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._startButton, this._loadButton, this._closeButton});
    }

    private void drawSettingsMenu(ViewSettings settings) {
        ViewUtil.setBackgroundColor(this, ViewConfig._transparentMenus ? 0.0f : 1.0f);
        this._consumablePage = settings.getShell();
        this.resetBack();
        this._menuInteract.setVisible(false);
        this.drawCurrentShellToSettingsMenu();
        int x = this._settingsMenu.getSizeX();
        int y = this._settingsMenu.getSizeY();
        this.checkSettings();
        this._closeButton.setLocX(158);
        this._closeButton.setVisible(true);
        this._upButton.setLoc(58, 26);
        this._upButton.setVisible(true);
        this._downButton.setLoc(58, 134);
        this._downButton.setVisible(true);
        this._focusLabel.setVisible(true);
        this._onTopLabel.setVisible(true);
        this._smallScale.setVisible(true);
        this._mediumScale.setVisible(true);
        this._largeScale.setVisible(true);
        this._soundLabel.setVisible(true);
        this._settingsMenu.setVisible(true);
        this._display.setSize(x, y);
        this._mainDisplay.setSize(x, y);
        this._interact.setSize(x, y);
        this._mainInteract.setSize(x, y);
        this._mainInteract.setLocation(0, 0);
        this._menuInteract.setSize(x, y);
        this._back.setSize(x, y);
        this._back.setLocation(0, 0);
        this.setSize(x, y);
        this._weather.getOverlay().setVisible(false);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._upButton, this._downButton, this._smallScale, this._mediumScale, this._largeScale, this._soundLabel, this._focusLabel, this._onTopLabel, this._closeButton});
    }

    public void drawCurrentShellToSettingsMenu() {
        ImageIcon i = this._settingsMenu.getAltSprite("settingsMenu");
        Shell s = this._controller.getShells().get(this._consumablePage);
        BufferedImage menu = ViewUtil.createBuffImage(i);
        Graphics2D g2 = menu.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        BufferedImage bShell = ViewUtil.getResource(this.MOD_FOLDER, this.RESOURCES_FOLDER, s.getFileName());
        bShell = bShell.getSubimage(0, 0, s.getSize()[0], s.getSize()[1]);
        Icon newShell = ViewUtil.resizeImage(bShell, 116 * this.getScale(), 90 * this.getScale());
        g2.drawImage(ViewUtil.createBuffImage(newShell), null, 14 * this.getScale(), 41 * this.getScale());
        g2.dispose();
        this._settingsMenu.setIcon(new ImageIcon(menu));
    }

    private void checkSettings() {
        this.checkSound();
        if (this._controller.getModel().getSettings().isFocus()) {
            this._focusLabel.setAltIcon("callLabel");
        } else {
            this._focusLabel.setAltIcon("tCallLabel");
        }
        if (this._controller.getModel().getSettings().isOnTop()) {
            this._onTopLabel.setAltIcon("onTopLabel");
        } else {
            this._onTopLabel.setAltIcon("tOnTopLabel");
        }
        switch (this._controller.getNewScale()) {
            case 1: {
                this._mediumScale.setAltIcon("tMediumSelect");
                this._largeScale.setAltIcon("tLargeSelect");
                this._smallScale.setAltIcon("smallSelect");
                break;
            }
            case 2: {
                this._smallScale.setAltIcon("tSmallSelect");
                this._largeScale.setAltIcon("tLargeSelect");
                this._mediumScale.setAltIcon("mediumSelect");
                break;
            }
            case 3: {
                this._smallScale.setAltIcon("tSmallSelect");
                this._mediumScale.setAltIcon("tMediumSelect");
                this._largeScale.setAltIcon("largeSelect");
            }
        }
    }

    private void checkSound() {
        if (this._controller.getModel().getSettings().isSound()) {
            this._soundLabel.setAltIcon("soundTransp");
        } else {
            this._soundLabel.setAltIcon("soundOffTransp");
        }
    }

    private void drawNewGameMenu() {
        this.resetBack();
        this._closeButton.setLocX(193);
        this._closeButton.setLocY(1);
        this._closeButton.setVisible(true);
        this._fastClockDisplay.setVisible(true);
        this._fastClockButton.setVisible(true);
        this._timeSkipButton.setAltIcon(this._controller.getModel().getDigimon().getTimeSkip() ? "timeSkip" : "tTimeSkip");
        this._timeSkipButton.setVisible(this._controller.getModel().getTime().getFastMod() == 1);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this.checkEggLabel(this._controller.getModel().getDigimon().getEvolution().getStartingDigimon());
        this._eggLabel.setSize(48, 48);
        this._eggLabel.setLocX(133);
        this._eggLabel.setLocY(27);
        this._eggLabel.setVisible(true);
        this._colonLabel.setVisible(true);
        this._plusHoursButton.setVisible(true);
        this._minusHoursButton.setVisible(true);
        this._plusMinutesButton.setVisible(true);
        this._minusMinutesButton.setVisible(true);
        this.setTime();
        this._hoursPane.setVisible(true);
        this._minutesPane.setVisible(true);
        this._enterButton.setLocX(178);
        this._enterButton.setLocY(85);
        this._enterButton.setVisible(true);
        int x = this._newGameMenu.getSizeX();
        int y = this._newGameMenu.getSizeY();
        this._display.setSize(x, y);
        this._mainDisplay.setSize(x, y);
        this._interact.setSize(x, y);
        this._mainInteract.setSize(x, y);
        this._menuInteract.setSize(x, y);
        this._back.setSize(x, y);
        this._back.setLocation(0, 0);
        this.setSize(x, y);
        this._newGameMenu.setVisible(true);
        ViewUtil.centerMain(this);
        this._newGameMenu.requestFocus();
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>(Arrays.asList(this._plusHoursButton, this._minusHoursButton, this._plusMinutesButton, this._minusMinutesButton, this._fastClockButton, this._leftButton, this._rightButton, this._enterButton, this._closeButton));
        if (this._timeSkipButton.isVisible()) {
            obj.add(5, this._timeSkipButton);
        }
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawSetDifficultyMenu() {
        this.resetBack();
        EvolutionInfo mon = this._controller.getModel().getDigimon().getEvolution().getDigimon(ViewConfig._classicModeDigimon);
        this.setOppSprites(this.getOppSet(mon.getNewStage(), mon.getNewSpriteSet(), mon.getNewSpriteNum()));
        this._opponent.setSize(48, 48);
        this._opponent.setLoc(19, 59);
        mon = this._controller.getModel().getDigimon().getEvolution().getDigimon(ViewConfig._hardModeDigimon);
        SpriteObj character = this.getOppSet(mon.getNewStage(), mon.getNewSpriteSet(), mon.getNewSpriteNum());
        this._character.setSpriteSheet(character.getSpriteSheet());
        this._character.setSpriteLoc(character.getSpriteLoc());
        mon = this._controller.getModel().getDigimon().getEvolution().getDigimon(ViewConfig._hardcoreModeDigimon);
        character = this.getOppSet(mon.getNewStage(), mon.getNewSpriteSet(), mon.getNewSpriteNum());
        this._eggLabel.setSpriteSheet(character.getSpriteSheet());
        this._eggLabel.setSpriteLoc(character.getSpriteLoc());
        this._eggLabel.setSpriteNum(0);
        this._eggLabel.setSize(48, 48);
        this._eggLabel.setLoc(161, 59);
        this._character.setSpriteNum(0);
        this._character.setSize(48, 48);
        this._character.setLoc(90, 59);
        this._character.drawNumMirror(0, false);
        this._opponent.drawNumMirror(0, false);
        this._eggLabel.drawNumMirror(0, false);
        this._closeButton.setLocX(212);
        this._closeButton.setLocY(1);
        this._closeButton.setVisible(true);
        int x = this._difficultyMenu.getSizeX();
        int y = this._difficultyMenu.getSizeY();
        this._display.setSize(x, y);
        this._mainDisplay.setSize(x, y);
        this._interact.setSize(x, y);
        this._mainInteract.setSize(x, y);
        this._menuInteract.setSize(x, y);
        this._back.setSize(x, y);
        this._back.setLocation(0, 0);
        this.setSize(x, y);
        this._difficultyMenu.setVisible(true);
        ViewUtil.centerMain(this);
        this._difficultyMenu.requestFocus();
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._opponent, this._character, this._eggLabel, this._closeButton});
    }

    private void drawSaveLoadMenu(String title) {
        ViewUtil.setBackgroundColor(this, ViewConfig._transparentMenus ? 0.0f : 1.0f);
        this.resetBack();
        this._userInputTitle.setText(title);
        this._userInputTitle.setVisible(true);
        this._closeButton.setLocX(167);
        this._closeButton.setLocY(1);
        this._closeButton.setVisible(true);
        this._enterButton.setLocX(149);
        this._enterButton.setLocY(39);
        this._enterButton.setVisible(true);
        this._stringPane.setVisible(true);
        this._stringPane.setText("");
        this._stringPane.requestFocus();
        int x = this._saveLoadMenu.getSizeX();
        int y = this._saveLoadMenu.getSizeY();
        this._display.setSize(x, y);
        this._mainDisplay.setSize(x, y);
        this._interact.setSize(x, y);
        this._mainInteract.setSize(x, y);
        this._menuInteract.setSize(x, y);
        this._back.setSize(x, y);
        this._back.setLocation(0, 0);
        this.setSize(x, y);
        this._saveLoadMenu.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new Component[]{this._stringPane, this._enterButton, this._closeButton});
    }

    public void drawMainMenu() {
        this.setSpriteCharDefault();
        this._hoursPane.setLocation((59 - this._xPad) * this.getScale(), (59 - this._yPad) * this.getScale());
        this._minutesPane.setLocation(this._hoursPane.getX() + 40 * this.getScale(), (59 - this._yPad) * this.getScale());
        this._colonLabel.setLocX(this._hoursPane.getX() / this.getScale() + 30);
        this._colonLabel.setLocY(69 - this._yPad);
        this._menuInteract.setVisible(true);
        this._evolutionTreeButton.setVisible(true);
        this._mapButton.setVisible(true);
        this._clockButton.setVisible(true);
        this._settingsButton.setVisible(true);
        this._saveButton.setVisible(true);
        this._back.setVisible(true);
        this._shell.setVisible(true);
        this._background.setVisible(true);
        this._mainBackground.setVisible(true);
        this._startMenu.setVisible(false);
        this._hostNameMenu.setVisible(false);
        this._settingsMenu.setVisible(false);
        this.enableMainMenu();
        this.setSizes(this._controller.getCurrentShell());
    }

    public void setupMainMenuAndInteractiveButtons() {
        try {
            this._keyboard.setCursorPosition(-1);
            this._gameButton.setAltIcon("tGameButton");
            if (this._controller.getModel().getDigimon().getAlive()) {
                this._keyboard.addInteractiveButtons(new SpriteObj[]{this._statusButton, this._feedButton, this._digisoulButton, this._gameButton, this._battleButton, this._washButton, this._lightButton, this._firstAidButton, this._tempButton, this._character, this._evolutionTreeButton, this._mapButton, this._clockButton, this._settingsButton, this._saveButton});
            } else {
                this._keyboard.setCursorPosition(0);
                this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton, this._statusButton, this._feedButton, this._digisoulButton, this._gameButton, this._battleButton, this._washButton, this._lightButton, this._firstAidButton, this._tempButton, this._evolutionTreeButton, this._mapButton, this._clockButton, this._settingsButton, this._saveButton});
            }
        }
        catch (NullPointerException nullPointerException) {
            // empty catch block
        }
    }

    private void setSizes(Shell s) {
        int width = s.getSize()[0];
        int height = s.getSize()[1];
        int x = s.getScreenShellLoc()[0] * this.getScale();
        int y = s.getScreenShellLoc()[1] * this.getScale();
        this._mainBackground.setSize(width, height);
        this.setSize(width *= this.getScale(), height *= this.getScale());
        this._display.setSize(width, height);
        this._mainDisplay.setSize(104 * this.getScale(), 60 * this.getScale());
        this._mainDisplay.setLocation(x, y + 20 * this.getScale());
        this._overlay.setSize(this._mainDisplay.getWidth(), this._mainDisplay.getHeight());
        this._overlay.setLocation(this._mainDisplay.getX(), this._mainDisplay.getY());
        this._weather.setOverlaySize(this._mainDisplay.getWidth(), this._mainDisplay.getHeight());
        this._weather.setOverlayLocation(0, 0);
        this._interact.setSize(width, height);
        this._menuInteract.setSize(width, height);
        this._mainInteract.setSize(this._mainDisplay.getWidth(), this._mainDisplay.getHeight());
        this._mainInteract.setLocation(this._mainDisplay.getX(), this._mainDisplay.getY());
        this._back.setSize(this._background.getWidth(), this._background.getHeight());
        this._back.setLocation(x, y);
        this._shell.setSize(width, height);
    }

    public void drawRestartMenu() {
        this._restartLabel.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(80 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(80 - this._yPad);
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    public void drawEggMenu() {
        this._consumablePage = 0;
        this._backButton.setVisible(true);
        this._eggLabel.setSize(48, 48);
        this._eggLabel.setLoc(54 - this._xPad, 62 - this._yPad);
        this._leftButton.setLoc(40 - this._xPad, 79 - this._yPad);
        this._rightButton.setLoc(104 - this._xPad, 79 - this._yPad);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this._eggLabel.setVisible(true);
        this.checkEggLabel(this._controller.getModel().getDigimon().getEvolution().getRestartDigimon());
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._rightButton, this._eggLabel});
    }

    private void disableMainMenu() {
        if (this._currentAnim == Enum.State.Idling || !Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentAnim)) {
            this._statusButton.setIsEnabled(false);
            this._saveButton.setIsEnabled(false);
            this._saveButton.setAltIcon(0);
            this._settingsButton.setIsEnabled(false);
            this._settingsButton.setAltIcon(0);
            this._keyboard.clearInteractiveButtons();
            this._statusButton.setAltIcon(0);
            this._feedButton.setIsEnabled(false);
            this._feedButton.setAltIcon(0);
            this._digisoulButton.setIsEnabled(false);
            this._digisoulButton.setAltIcon(0);
            this._gameButton.setIsEnabled(false);
            this._gameButton.setAltIcon(0);
            this._battleButton.setIsEnabled(false);
            this._battleButton.setAltIcon(0);
            this._washButton.setIsEnabled(false);
            this._washButton.setAltIcon(0);
            this._lightButton.setIsEnabled(false);
            this._lightButton.setAltIcon(0);
            this._tempButton.setIsEnabled(false);
            this._tempButton.setAltIcon(0);
            this._firstAidButton.setIsEnabled(false);
            this._firstAidButton.setAltIcon(0);
            this._evolutionTreeButton.setIsEnabled(false);
            this._evolutionTreeButton.setAltIcon(0);
            this._mapButton.setIsEnabled(false);
            this._mapButton.setAltIcon(0);
            this._clockButton.setIsEnabled(false);
            this._clockButton.setAltIcon(0);
        }
    }

    public void enableMainMenu() {
        this._statusButton.setIsEnabled(true);
        this._feedButton.setIsEnabled(true);
        this._digisoulButton.setIsEnabled(true);
        this._gameButton.setIsEnabled(true);
        this._battleButton.setIsEnabled(true);
        this._washButton.setIsEnabled(true);
        this._lightButton.setIsEnabled(true);
        this._tempButton.setIsEnabled(true);
        this._firstAidButton.setIsEnabled(true);
        this._evolutionTreeButton.setIsEnabled(true);
        this._mapButton.setIsEnabled(true);
        this._clockButton.setIsEnabled(true);
        this._settingsButton.setIsEnabled(true);
        this._saveButton.setIsEnabled(true);
        this.setupMainMenuAndInteractiveButtons();
    }

    private void drawSaveExitValidation() {
        this._surrenderOption.setVisible(false);
        this._surrenderOption.setSize(120, 18);
        this._surrenderOption.removeIcon();
        this._surrenderOption.setText("Save & Exit?");
        this._surrenderOption.setLoc(3, 60 - this._yPad);
        this._surrenderOption.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(84 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(84 - this._yPad);
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void drawSaveMenu(PhysicalState digimon) {
        this._saveOption.drawNumMirror(0, false);
        this._saveOption.setVisible(true);
        this._quitOption.drawNumMirror(2, false);
        this._quitOption.setVisible(true);
        this._backButton.setVisible(true);
        this._backButton.setVisible(true);
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        obj.add(this._saveOption);
        obj.add(this._quitOption);
        if (digimon.getClock().getFastMod() == 1) {
            if (digimon.getTimeSkip()) {
                this._timeSkipButton.setAltIcon("timeSkip");
            } else {
                this._timeSkipButton.setAltIcon("tTimeSkip");
            }
            this._timeSkipButton.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._timeSkipButton.getWidth() / this.getScale(), this._mainDisplay.getHeight() / this.getScale() - this._timeSkipButton.getHeight() / this.getScale() - 1);
            this._timeSkipButton.setVisible(true);
            obj.add(this._timeSkipButton);
        } else {
            this._timeSkipButton.setVisible(false);
        }
        obj.add(this._backButton);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawDigimemoryValidation() {
        this._surrenderOption.setVisible(false);
        this._surrenderOption.setSize(100, 18);
        this._surrenderOption.removeIcon();
        this._surrenderOption.setText("Overwrite?");
        this._surrenderOption.setLoc(10, 60 - this._yPad);
        this._surrenderOption.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(84 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(84 - this._yPad);
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void drawPraiseMenu() {
        ArrayList<SpriteObj> obj;
        if (this._controller.getModel().getDigimon().getIsHome()) {
            this._optionButton.setAltIcon("tAssistant");
            this._optionButton.setSize(13, 13);
            this._optionButton.setLoc(this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale() - 3, 3);
            this._optionButton.setVisible(true);
        }
        this._inventoryButton.setVisible(true);
        this._foodShopButton.setVisible(true);
        if (this._controller.getModel().getDigimon().getAlive()) {
            this._praiseButton.setSize(28, 28);
            this._praiseButton.setAltIcon("praiseTransp");
            this._praiseButton.setLocX(52 - this._xPad);
            this._praiseButton.setLocY(71 - this._yPad);
            this._scoldButton.setVisible(true);
            obj = new ArrayList<SpriteObj>(Arrays.asList(this._inventoryButton, this._foodShopButton, this._praiseButton, this._scoldButton, this._optionButton, this._backButton));
        } else {
            this._praiseButton.setSize(48, 48);
            this._praiseButton.setAltIcon("tRestart");
            this._praiseButton.setLocX(41);
            this._praiseButton.setLocY(6);
            obj = new ArrayList<SpriteObj>(Arrays.asList(this._inventoryButton, this._foodShopButton, this._praiseButton, this._backButton));
        }
        this._praiseButton.setVisible(true);
        this._backButton.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawDataClock() {
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this.checkTime();
        this._timeLabel.setVisible(true);
        this.checkSeason();
        this._seasonLabel.setLoc(0, this._mainInteract.getHeight() / this.getScale() - this._seasonLabel.getSizeY() / this.getScale());
        this._seasonLabel.setVisible(true);
        this.checkTemp();
        this._tempLabel.setLoc(this._seasonLabel.getSizeX() / this.getScale() + 3 + this._seasonLabel.getLocX() / this.getScale(), 3 + this._seasonLabel.getLocY() / this.getScale());
        this._tempLabel.setVisible(true);
        this._hoursPane.setFont(this._bit.deriveFont((float)(48 * this.getScale())));
        this._minutesPane.setFont(this._bit.deriveFont((float)(48 * this.getScale())));
        this._colonLabel.setFont(this._bit.deriveFont((float)(60 * this.getScale())));
        this._hoursPane.setVisible(true);
        this._minutesPane.setVisible(true);
        this._colonLabel.setVisible(true);
        this._ticLabel.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
    }

    private void drawDataTemp() {
        this._moodLabel.setLocX(105 - this._xPad);
        this._moodLabel.setLocY(54 - this._yPad);
        this._tempButton.setVisible(true);
        this._frame = 0;
        this._backButton.setVisible(true);
        this.setupTempMenu(this._controller.getModel().getDigimon().getTemp());
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._tempBar});
    }

    private void setupCurrentTemp(byte temp) {
        if (temp == 100) {
            this._currentTemp.setLocX(39);
        } else if (temp < 10) {
            this._currentTemp.setLocX(48);
        } else {
            this._currentTemp.setLocX(43);
        }
        this._currentTemp.setText(ViewUtil.getCenteredText("" + temp));
        this._currentTemp.setVisible(true);
    }

    private void setupTempMenu(byte temp) {
        this.setupTempBar(temp);
        this.setupCurrentTemp(temp);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.setupTempArrows(digimon);
    }

    private void setupTempBar(byte temp) {
        this._tempBar.setVisible(true);
        this._tempFill.setVisible(true);
        double newSize = (double)temp / 100.0 * this._tempFillDefaultSize;
        this._tempFill.setWidth((int)newSize);
        this._mainDisplay.repaint();
    }

    private void setupTempArrows(PhysicalState digimon) {
        if (digimon.getTempGoal() <= 100) {
            if (digimon.getTempGoal() > digimon.getTemp()) {
                this._tempArrow.setLoc(this._mainDisplay.getWidth() / this.getScale() - 39, 7 + this._currentTemp.getLocY() / this.getScale());
                this._tempArrow.setAltIcon("selectMirror");
                this._tempArrow.setVisible(true);
            } else if (digimon.getTempGoal() < digimon.getTemp()) {
                this._tempArrow.setLoc(34, 7 + this._currentTemp.getLocY() / this.getScale());
                this._tempArrow.setAltIcon("select");
                this._tempArrow.setVisible(true);
            } else {
                this._tempArrow.setVisible(false);
            }
        } else {
            this._tempArrow.setVisible(false);
        }
    }

    private void checkAdventureDetails() {
        int fullSize = 93;
        int sectionWidth = 6;
        double totalSections = 16.0;
        WorldMap world = this._controller.getModel().getDigimon().getWorld();
        double location = world.getCurrentZone().getCurrentLocation();
        double maxLocation = world.getCurrentZone().getTotalSteps();
        int currentSection = (int)(totalSections * (location / maxLocation));
        int newSize = currentSection * sectionWidth;
        int newLoc = this._zoneDetail.getLocX() / this.getScale() + 3 + (fullSize - newSize);
        this._adventureBar.setLocation(newLoc * this.getScale(), this._zoneDetail.getLocY() + 3 * this.getScale());
        this._adventureBar.setWidth(newSize * this.getScale());
        byte life = world.getAdventureLife();
        newSize = 16 * life;
        this._exerciseLabel.setAltIcon("emptyHearts");
        this._exerciseLabel.setSizeX(48);
        this._exerciseLabel.setLoc(54 - this._xPad, 99 - this._yPad);
        this._exerciseLabel.setVisible(true);
        this._fullExercise.setAltIcon("fullHearts");
        this._fullExercise.setLoc(54 - this._xPad, 99 - this._yPad);
        this._fullExercise.setSizeX(newSize);
        this._fullExercise.setVisible(true);
        this._townLabel.setLoc(this._zoneDetail.getLocX() / this.getScale(), this._zoneDetail.getLocY() / this.getScale() - this._townLabel.getSizeY() / this.getScale());
    }

    private void checkTemp() {
        byte temp = (byte)this._controller.getModel().getDigimon().getAdjustedDayTemp(this._controller.getModel().getDigimon().getDayTemp(), this._controller.getModel().getDigimon().getCurrentHabitat());
        if (temp <= 10) {
            this._tempLabel.drawNumMirror(0, false);
        } else if (temp >= 11 && temp <= 32) {
            this._tempLabel.drawNumMirror(1, false);
        } else if (temp >= 33 && temp <= 66) {
            this._tempLabel.drawNumMirror(2, false);
        } else if (temp >= 67 && temp <= 89) {
            this._tempLabel.drawNumMirror(3, false);
        } else if (temp >= 90) {
            this._tempLabel.drawNumMirror(4, false);
        }
    }

    private void checkTime() {
        switch (this._controller.getModel().getDigimon().checkTime(this._controller.getModel().getTime().getHours())) {
            case Morning: {
                this._timeLabel.setAltIcon("morning");
                break;
            }
            case Noon: {
                this._timeLabel.setAltIcon("noon");
                break;
            }
            case Night: {
                this._timeLabel.setAltIcon("night");
            }
        }
    }

    private void checkSeason() {
        switch (this._controller.getModel().getDigimon().getSeason()) {
            case Spring: {
                this._seasonLabel.setAltIcon("spring");
                break;
            }
            case Summer: {
                this._seasonLabel.setAltIcon("summer");
                break;
            }
            case Fall: {
                this._seasonLabel.setAltIcon("fall");
                break;
            }
            case Winter: {
                this._seasonLabel.setAltIcon("winter");
            }
        }
    }

    private void drawDataStatus() {
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this._agePanel.setBounds((28 - this._xPad) * this.getScale(), 2 * this.getScale(), 56 * this.getScale(), ViewConfig._fontSize * this.getScale());
        String age = Integer.toString(this._controller.getModel().getDigimon().getAge());
        this._agePanel.setText("Age " + (age.length() < 2 ? " " + age : age));
        this._agePanel.setVisible(true);
        this._weightLabel.setLocX(this._agePanel.getX() / this.getScale() + this._agePanel.getWidth() / this.getScale());
        this._weightLabel.setLocY(4 + this._agePanel.getY() / this.getScale());
        this.checkWeight();
        this._weightLabel.setVisible(true);
        this._weightPanel.setBounds(this._weightLabel.getLocX() + this._weightLabel.getSizeX() + 3 * this.getScale(), 2 * this.getScale(), 60 * this.getScale(), ViewConfig._fontSize * this.getScale());
        String weight = Integer.toString(this._controller.getModel().getDigimon().getWeight());
        if (weight.length() < 3) {
            String newWeight = " " + weight;
            if (weight.length() < 2) {
                newWeight = " " + newWeight;
            }
            weight = newWeight;
        }
        this._weightPanel.setText(weight);
        this._weightPanel.setVisible(true);
        this._typeLabel.setText("Attrb.");
        this._rightButton.setAltIcon("tSmall");
        this.drawType();
        this._rightButton.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton, this._rightButton});
    }

    private void drawTrainingSelect() {
        this._backButton.setVisible(true);
        this._gameButton.setIsEnabled(true);
        this._vaccineAttack.setLoc(-5 + this._mainDisplay.getWidth() / this.getScale() / 2, 4);
        this._vaccineAttack.setVisible(true);
        this._dataAttack.setLoc(this._vaccineAttack.getX() / this.getScale() - 24, 13 + this._mainDisplay.getHeight() / this.getScale() / 2);
        this._dataAttack.setVisible(true);
        this._virusAttack.setLoc(this._vaccineAttack.getX() / this.getScale() + 24, this._dataAttack.getY() / this.getScale());
        this._virusAttack.setVisible(true);
        this._practiceOption.setLoc(this._vaccineAttack.getX() / this.getScale(), 23 + this._vaccineAttack.getY() / this.getScale());
        this._practiceOption.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton, this._vaccineAttack, this._dataAttack, this._virusAttack, this._practiceOption});
    }

    private void getHPText(int hp, int max) {
        String num = hp + " / " + max;
        float size = 31.0f * (float)this.getScale();
        this._consumableDescription.setText("<html><div style=\"width:" + 84 * this.getScale() + "px;\"><div style=\"margin-top:" + 5 * this.getScale() + "px;text-align:center;display:inline-block;font-size:" + size + "px;\"><div>HP</div>" + num + "</div></div></html>");
        this._consumableDescription.setVisible(true);
    }

    private void drawDataHP(int hp, int max) {
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this.setupDataHP(hp, max);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton, this._healthBarFull});
    }

    private void setupDataHP(int hp, int max) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.getHPText(hp, max);
        this.checkHealth(hp, max);
        this.recoveryAnim(digimon.isFullyRecovered());
        this._recoveryLabel.setLoc(95 - this._xPad, 9);
        this._recoveryLabel.setVisible(true);
        this._healthBar.setLocX(26 - this._xPad);
        this._healthBarFull.setLocX(26 - this._xPad);
        this._healthBarFull.setVisible(true);
        this._healthBar.setVisible(true);
    }

    private void drawDataPower() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        String level = "" + digimon.getDigimonLevel();
        this._consumableDescription.setText("<html><div style=\"width:" + 128 * this.getScale() + "px;text-align:right;\"><div style=\"text-align:center;display:inline-block;font-size:" + 24 * this.getScale() + "px;\"><div>LV</div>" + level + "</div></div></html>");
        this._consumableDescription.setVisible(true);
        this._vaccineAttack.setLoc(this._vaccinePowerLabel.getLocX() / this.getScale() - this._vaccineAttack.getSizeX() / this.getScale() - 6, this._vaccinePowerLabel.getLocY() / this.getScale() + 7);
        this._vaccineAttack.setVisible(true);
        this._vaccinePowerLabel.setText("" + digimon.getVaccinePower());
        this._vaccinePowerLabel.setVisible(true);
        this._dataAttack.setLoc(this._vaccineAttack.getLocX() / this.getScale(), this._dataPowerLabel.getLocY() / this.getScale() + 7);
        this._dataAttack.setVisible(true);
        this._dataPowerLabel.setText("" + digimon.getDataPower());
        this._dataPowerLabel.setVisible(true);
        this._virusAttack.setLoc(this._vaccineAttack.getLocX() / this.getScale(), this._virusPowerLabel.getLocY() / this.getScale() + 7);
        this._virusAttack.setVisible(true);
        this._virusPowerLabel.setText("" + digimon.getVirusPower());
        this._virusPowerLabel.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton, this._vaccineAttack, this._dataAttack, this._virusAttack});
    }

    private void drawDataIntolerant(Enum.Food food) {
        this._consumablePage = 0;
        this._statusButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._personLabel.setLocX(this._backButton.getLocX() / this.getScale() + this._backButton.getWidth() / this.getScale() + 3);
        this._personLabel.setLocY(60 - this._yPad);
        this._personLabel.setText("Intolerant");
        this._personLabel.setVisible(true);
        this._favFoodLabel.setLoc(66 - this._xPad, 86 - this._yPad);
        this._leftButton.setLoc(1, this._favTimeLabel.getLocY() / this.getScale() + 3);
        this._rightButton.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._rightButton.getWidth() / this.getScale() + 4, this._leftButton.getLocY() / this.getScale());
        this.setupFavFoodLabel(food);
        this._favFoodLabel.setVisible(true);
        this._leftButton.setAltIcon("tSmall");
        this._rightButton.setAltIcon("tSmall");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton, this._favFoodLabel, this._rightButton, this._leftButton});
    }

    private void drawDataFavorites(Enum.Time time, Enum.Food food, Enum.Attribute attribute, String s) {
        this._statusButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._personLabel.setLocX(this._backButton.getLocX() / this.getScale() + this._backButton.getWidth() / this.getScale() + 3);
        this._personLabel.setLocY(60 - this._yPad);
        this._personLabel.setText(s);
        this._personLabel.setVisible(true);
        this._favTimeLabel.setLoc(34 - this._xPad, 83 - this._yPad);
        this._favFoodLabel.setLoc(66 - this._xPad, 86 - this._yPad);
        this._favAttLabel.setLoc(93 - this._xPad, 84 - this._yPad);
        this._leftButton.setLoc(1, this._favTimeLabel.getLocY() / this.getScale() + 3);
        this._rightButton.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._rightButton.getWidth() / this.getScale() + 5, this._leftButton.getLocY() / this.getScale());
        this.checkFavDisplay(time, food, attribute);
        this._leftButton.setAltIcon("tSmall");
        this._rightButton.setAltIcon("tSmall");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton, this._rightButton, this._leftButton});
    }

    private void drawDataPerson() {
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this._optionButton.setSize(13, 13);
        this._optionButton.setLoc(this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale() - 3, 3);
        this._optionButton.setAltIcon("favoriteMenuTransp");
        this._optionButton.setVisible(true);
        this._personLabel.setLocX(29 - this._xPad);
        this._personLabel.setLocY(60 - this._yPad);
        this._personLabel.setText(this.checkPersonality());
        this._personLabel.setVisible(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._favAttLabel.setLoc(98 - this._xPad, 84 - this._yPad);
        this._favTimeLabel.setLoc(29 - this._xPad, 83 - this._yPad);
        this._favFoodLabel.setLoc(66 - this._xPad, 86 - this._yPad);
        this.checkFavDisplay(digimon.getTimeRanks().getUnlockedFav() ? digimon.getFavTime() : null, digimon.getFoodRanks().getUnlockedFav() ? digimon.getFavFood() : null, digimon.getAttributeRanks().getUnlockedFav() ? digimon.getFavAtt() : null);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton, this._personLabel, this._optionButton});
    }

    private void drawDataPersonDetail(PhysicalState digimon) {
        String g;
        this._statusButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._personLabel.setLocX(this._backButton.getLocX() / this.getScale() + this._backButton.getWidth() / this.getScale() + 1);
        this._personLabel.setLocY(57 - this._yPad);
        this._personLabel.setVisible(true);
        String d = digimon.getDisposition() > 0 ? "Positive" : (digimon.getDisposition() < 0 ? "Negative" : "Neutral");
        d = d + " Disposition";
        String string = digimon.getGlutton() > 0 ? "High Appetite" : (g = digimon.getGlutton() < 0 ? "Low Appetite" : "Normal Appetite");
        String a = digimon.getRestless() > 0 ? "High Activity" : (digimon.getRestless() < 0 ? "Low Activity" : "Normal Activity");
        this.drawConsumableDescriptionMargin("", "<br>&nbsp;-&nbsp;" + d + "<br>&nbsp;-&nbsp;" + g + "<br>&nbsp;-&nbsp;" + a + "<br>", -1);
    }

    private void checkWeight() {
        Enum.Weight weight = this._controller.getModel().getDigimon().getOverweight();
        switch (weight) {
            case Over: {
                this._weightLabel.setAltIcon("weightOver");
                break;
            }
            case Healthy: {
                this._weightLabel.setAltIcon("weightNormal");
                break;
            }
            case Under: {
                this._weightLabel.setAltIcon("weightUnder");
            }
        }
    }

    private void drawDataHealth(boolean isHunger) {
        int y;
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        int heartSize = 16;
        obj.add(this._menuButton);
        int x = Config._showHungerStrengthNumber ? 20 : 24;
        int n = y = Config._showHungerStrengthNumber ? 29 : 37;
        if (isHunger) {
            this.showHunger(digimon, heartSize, x, y);
            this.drawHealthDescription("Hunger", digimon.getHunger(), digimon.getOvereatLimit());
            obj.add(this._optionButton);
        } else {
            this.showStrength(digimon, heartSize, x, y);
            this.drawHealthDescription("Strength", digimon.getExercise(), digimon.getExerciseLimit());
        }
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawCaloriesDescription(String stat, int current, int max) {
        String num = Config._showCaloriesNumber ? current + " / " + max : "";
        this.drawHealthDescription(stat, num);
    }

    private void drawHealthDescription(String stat, int current, int max) {
        String num = Config._showHungerStrengthNumber ? current + " / " + max : "";
        this.drawHealthDescription(stat, num);
    }

    private void drawHealthDescription(String stat, String num) {
        this._messageDisplay.setText("<html><div style=\"height:" + 33 * this.getScale() + "px;font-size:" + 28 * this.getScale() + "px;\">" + stat + "</div><div style=\"width:" + 126 * this.getScale() + "px;text-align:right;\"><div style=\"text-align:center;display:inline-block;font-size:" + 18 * this.getScale() + "px;\">" + num + "</div></div></html>");
        this._messageDisplay.setVisible(true);
    }

    private void drawFoodNutrition(byte protein, byte mineral, byte vitamin, byte total) {
        this.drawDataNutrition(protein, mineral, vitamin, total, total, total);
    }

    private void drawDataNutrition(byte protein, byte mineral, byte vitamin) {
        this.drawDataNutrition(protein, mineral, vitamin, Config._maxProtein, Config._maxMineral, Config._maxVitamin);
        this._frame = 0;
        this._recoveryLabel.setLoc(29 - this._xPad, 69 + (Config._showCaloriesMenu ? 5 : 10) - this._yPad);
        this._recoveryLabel.setVisible(true);
    }

    private void drawDataCalories(PhysicalState digimon) {
        this._statusButton.setIsEnabled(true);
        int calories = digimon.getCalories();
        this.drawCaloriesDescription("&nbsp; Calories", calories, digimon.getMaxCalories());
        this.drawCaloriesDisplay(calories += Math.abs(digimon.getMinCalories()), digimon);
    }

    private void drawFoodCalories(int calories, PhysicalState digimon) {
        this._feedButton.setIsEnabled(true);
        this.drawHealthDescription("&nbsp; Calories", Config._showCaloriesNumber ? "+" + calories : "");
        this.drawCaloriesDisplay(calories, digimon);
    }

    private void drawCaloriesDisplay(int calories, PhysicalState digimon) {
        this._backButton.setVisible(true);
        double totalCalories = Math.abs(digimon.getMinCalories()) + digimon.getMaxCalories();
        double current = (double)calories / totalCalories;
        this.showIncrementalHearts(4.0 * current, 22, Config._showCaloriesNumber ? 26 : 33);
    }

    private void setFoodGroupIcon(int i) {
        this._foodLabel.setIcon(this.getFoodGroupIcon(i));
    }

    private Icon getFoodGroupIcon(int i) {
        FoodType c = this._controller.getModel().getDigimon().getFoodByID(ViewUtil.getFoodGroupNum(this._foodType.getType().get(i)));
        return ViewUtil.getFoodSheet(c, this.MOD_FOLDER, this.RESOURCES_FOLDER, this._controller.getModel().getSettings().getGameScale())[0];
    }

    private void drawDataNutrition(byte protein, byte mineral, byte vitamin, byte maxProtein, byte maxMineral, byte maxVitamin) {
        this._backButton.setVisible(true);
        switch (this._controller.getCurrentMenu()) {
            case Med_Nutrition: {
                this._firstAidButton.setIsEnabled(true);
                this.setFoodGroupIcon(0);
                this._foodLabel.setVisible(true);
                break;
            }
            case Data_Nutrition: {
                this._statusButton.setIsEnabled(true);
                this._foodLabel.setVisible(false);
                break;
            }
            default: {
                this._feedButton.setIsEnabled(true);
                this.setFoodGroupIcon(0);
                this._foodLabel.setVisible(true);
            }
        }
        this._messageDisplay.setText("<html><div style=\"text-align:center;height:" + 42 * this.getScale() + "px;width:" + 90 * this.getScale() + "px;font-weight:bold;\">P&nbsp;&nbsp;M&nbsp;&nbsp;V</div></html>");
        this._messageDisplay.setVisible(true);
        ViewUtil.centerObj(this._mainDisplay, this._foodLabel);
        this._foodLabel.setLocX(2);
        if (Config._showCaloriesMenu) {
            this._foodLabel.moveUp(3);
            this._optionButton.setSize(15, 15);
            ViewUtil.centerObj(this._foodLabel, this._optionButton);
            this._optionButton.setLocY(this._foodLabel.getLocY() / this.getScale() + 3 + this._foodLabel.getSizeY() / this.getScale());
            this._optionButton.setAltIcon("tCalories");
            this._optionButton.setVisible(true);
        } else {
            this._foodLabel.moveDown(4);
        }
        double pSize = (double)protein / (double)maxProtein;
        double mSize = (double)mineral / (double)maxMineral;
        double vSize = (double)vitamin / (double)maxVitamin;
        int size = 42;
        pSize = (double)size * pSize;
        mSize = (double)size * mSize;
        vSize = (double)size * vSize;
        if (pSize > 42.0) {
            pSize = 42.0;
        }
        if (mSize > 42.0) {
            mSize = 42.0;
        }
        if (vSize > 42.0) {
            vSize = 42.0;
        }
        this._proteinBar.setSizeY((int)pSize);
        this._mineralBar.setSizeY((int)mSize);
        this._vitaminBar.setSizeY((int)vSize);
        this._proteinBar.setLocY(-((int)pSize) + this._mainDisplay.getHeight() / this.getScale());
        this._mineralBar.setLocY(-((int)mSize) + this._mainDisplay.getHeight() / this.getScale());
        this._vitaminBar.setLocY(-((int)vSize) + this._mainDisplay.getHeight() / this.getScale());
        this._proteinBar.setVisible(true);
        this._mineralBar.setVisible(true);
        this._vitaminBar.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
    }

    private void drawDataHealthTrack() {
        this._backButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this.checkHealthTracker(this._controller.getModel().getDigimon().getPerfectWins());
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
    }

    private void drawDataEnergy() {
        this._menuButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.moodAnim(digimon.getCurrentMood());
        this.checkEnergy();
        this.checkSleep();
        String num = Config._showEnergyAmount ? digimon.getEnergy() + " / " + this._controller.getModel().getDigimon().getMaxEnergy() : "";
        this._sleepLabel.setVisible(true);
        this._energy.setVisible(true);
        this._energyLabel.setVisible(true);
        this._energyBar.setVisible(true);
        this._sleepLabel.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._sleepLabel.getWidth() / this.getScale() - 8, 1);
        this._energyLabel.setLocX(0);
        this._energyLabel.setLocY(3);
        this._energyBar.setLocX(30 - this._xPad);
        this._energyBar.setLocY(this._energyLabel.getLocY() / this.getScale() + 20);
        this._energy.setText(num);
        this._energy.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._energy.getWidth() / this.getScale(), this._energyLabel.getLocY() / this.getScale() + this._energyLabel.getHeight() / this.getScale() + 1);
        this._moodLabel.setLocX(8);
        this._moodLabel.setLocY(this._mainDisplay.getHeight() / this.getScale() - this._moodLabel.getHeight() / this.getScale());
        this.checkObedience();
        this._obedienceLabel.setVisible(true);
        this._obedienceFull.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
    }

    private void drawDataBattleLevels() {
        this._consumablePage = 0;
        this._backButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this._leftButton.setLoc(28 - this._xPad, 73 - this._yPad);
        this._rightButton.setLoc(116 - this._xPad, 73 - this._yPad);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this.drawLevelList(this._controller.getModel().getDigimon().getUniqueLevelFought());
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton, this._rightButton, this._leftButton});
    }

    private void drawLevelList(ArrayList<Integer> levels) {
        Collections.sort(levels);
        if (levels.size() <= 3) {
            this._leftButton.setVisible(false);
            this._rightButton.setVisible(false);
        } else {
            this._leftButton.setVisible(true);
            this._rightButton.setVisible(true);
        }
        PhysicalState digimon = this._controller.getModel().getDigimon();
        int start = this._consumablePage * 3;
        String first = this.levelTitle(levels, digimon, start);
        String second = this.levelTitle(levels, digimon, ++start);
        String third = this.levelTitle(levels, digimon, ++start);
        this._consumableDescription.setText("<html><div><p style=\"text-align:center;font-weight:bold;font-size:" + 16 * this.getScale() + "px;\">LVs Beaten</p><p style=\"text-align:center;font-weight:bold;width:" + 80 * this.getScale() + "px;font-size:" + 14 * this.getScale() + "px;\">" + first + "<br>" + second + "<br>" + third + "</p></div></html>");
        this._consumableDescription.setVisible(true);
    }

    private String levelTitle(ArrayList<Integer> levels, PhysicalState digimon, int start) {
        if (start >= 0 && start < levels.size()) {
            return "LV " + levels.get(start) + " : " + digimon.getLevelCount(levels.get(start));
        }
        return "&nbsp;";
    }

    private void drawDataBattles() {
        int i;
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        this._menuButton.setVisible(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        String winRate = " " + digimon.getWinRate() + "%";
        String battles = " " + digimon.getBattles();
        int length = 4 - battles.length();
        for (i = 0; i < length; ++i) {
            battles = "  " + battles;
        }
        length = 5 - winRate.length();
        for (i = 0; i < length; ++i) {
            winRate = "  " + winRate;
        }
        this._statusButton.setIsEnabled(true);
        this._battlesPanel.setText("Battles " + battles);
        this._battlesPanel.setVisible(true);
        obj.add(this._menuButton);
        if (!digimon.levelsFoughtIsEmpty()) {
            this._optionButton.setSize(15, 15);
            this._optionButton.setLoc(2, 74 - this._yPad);
            this._optionButton.setAltIcon("tBattleLevel");
            this._optionButton.setVisible(true);
            obj.add(this._optionButton);
        }
        this._winRatePanel.setText("Won " + winRate);
        this._winRatePanel.setVisible(true);
        String bits = NumberFormat.getIntegerInstance().format(this._controller.getModel().getDigimon().getBits());
        length = 8 - bits.length();
        for (int i2 = 0; i2 < length; ++i2) {
            bits = "  " + bits;
        }
        this._bitsPanel.setText(bits);
        this._bitsLabel.setRawLoc(3 * this.getScale(), 37 * this.getScale());
        this._bitsPanel.setSizeY(ViewConfig._fontSize);
        this._bitsPanel.setLocY(89 - this._yPad);
        this._bitsPanel.setLocX(this._bitsLabel.getLocX() / this.getScale() + 26);
        this._bitsPanel.setVisible(true);
        this._bitsLabel.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawFeedMenu() {
        this._feedButton.setIsEnabled(true);
        this._inventoryButton.setAltIcon("tInventory");
        this._foodShopButton.setAltIcon("tFoodShop");
        this._inventoryButton.setVisible(true);
        this._foodShopButton.setVisible(true);
        this._meatButton.setSize(24, 24);
        this._foodType = this._controller.getModel().getDigimon().getFoodByID(0);
        this.setFoodSet();
        this._meatButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
        this._meatButton.setLocX(56 - this._xPad);
        this._meatButton.setLocY(57 - this._yPad);
        this._meatButton.setVisible(true);
        this._foodType = this._controller.getModel().getDigimon().getFoodByID(1);
        this.setFoodSet();
        this._fishButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
        this._fishButton.setLocX(27 - this._xPad + this._meatButton.getSizeX() / this.getScale() + 37 + this._select.getSizeX() / this.getScale());
        this._fishButton.setLocY(57 - this._yPad);
        this._fishButton.setVisible(true);
        this._foodType = this._controller.getModel().getDigimon().getFoodByID(2);
        this.setFoodSet();
        this._fruitButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
        this._fruitButton.setLocX(56 - this._xPad);
        this._fruitButton.setLocY(60 - this._yPad + this._meatButton.getSizeY() / this.getScale());
        this._fruitButton.setVisible(true);
        this._foodType = this._controller.getModel().getDigimon().getFoodByID(3);
        this.setFoodSet();
        this._vegButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
        this._vegButton.setLocX(64 - this._xPad + this._fruitButton.getSizeX() / this.getScale() + this._select.getSizeX() / this.getScale());
        this._vegButton.setLocY(60 - this._yPad + this._fishButton.getSizeY() / this.getScale());
        this._vegButton.setVisible(true);
        this._backButton.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._inventoryButton, this._foodShopButton, this._meatButton, this._fishButton, this._fruitButton, this._vegButton, this._backButton});
    }

    private void drawBuySellValidation() {
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        this._backButton.setVisible(true);
        if (this.drawShop(this._controller.getCurrentMenu())) {
            this._tourneyOption.setText("Buy");
            this._tourneyOption.setLocX(58 - this._xPad);
            this._tourneyOption.setLocY(69 - this._yPad);
            this._tourneyOption.setSize(42, 24);
            this._tourneyOption.setVisible(true);
            this._multiOption.setText("Sell");
            this._multiOption.setLocX(this._tourneyOption.getLocX() / this.getScale());
            this._multiOption.setLocY(94 - this._yPad);
            this._multiOption.setSize(28, 18);
            this._multiOption.setVisible(true);
            obj.add(this._tourneyOption);
            obj.add(this._multiOption);
        }
        obj.add(this._backButton);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private boolean drawShop(Enum.Menu m) {
        this._backButton.setVisible(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        byte[] time = null;
        boolean isOpen = false;
        switch (m) {
            case Food_Buy_Sell_Validation: {
                this._backgroundAnim.checkBackNoAnim(digimon, m, this.getScale(), this._controller.getBattle());
                this._feedButton.setIsEnabled(true);
                time = digimon.getFoodShopTime();
                break;
            }
            case Item_Buy_Sell_Validation: {
                this._backgroundAnim.checkBackNoAnim(digimon, m, this.getScale(), this._controller.getBattle());
                this._statusButton.setIsEnabled(true);
                time = digimon.getItemShopTime();
                break;
            }
            case Habitat_Shop: {
                this._statusButton.setIsEnabled(true);
                time = digimon.getHabitatShopTime();
            }
        }
        isOpen = digimon.isShopOpen(time);
        if (!isOpen) {
            this._shopHours.setLocation(this._mainDisplay.getWidth() - 84 * this.getScale(), this._mainDisplay.getHeight() - 21 * this.getScale());
            this._shopHours.setVisible(true);
            this._roomEffect.setAltIcon("shopClosed");
            this._roomEffect.setVisible(true);
        } else if (m != Enum.Menu.Habitat_Shop) {
            this._shopHours.setLocation(this._mainDisplay.getWidth() - 84 * this.getScale(), -4 * this.getScale());
            this._shopHours.setVisible(true);
        }
        String t = "Hours: " + time[0] + "-" + time[1];
        this._shopHours.setText(t);
        return isOpen;
    }

    public ArrayList<ShopConsumable> drawFoodSaleInventory() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        ArrayList<ShopConsumable> sc = digimon.getSellableFood();
        this._feedButton.setIsEnabled(true);
        this.drawConsumableList(digimon.getFoodTypesAsConsumable(), sc, this._foodLabel, "Food", 6, 24, 24, this.getScale());
        return sc;
    }

    public void drawFoodInventory() {
        this._feedButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.drawConsumableList(digimon.getFoodTypesAsConsumable(digimon.getFoodOwned(true)), null, this._foodLabel, "Food", 6, 24, 24, this.getScale());
    }

    public void drawFoodShop() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._feedButton.setIsEnabled(true);
        this.drawConsumableList(digimon.getFoodTypesAsConsumable(), digimon.getHomeFoodShop(), this._foodLabel, "Food", 6, 24, 24, this.getScale());
    }

    private void setupList() {
        this._backButton.setVisible(true);
        this._leftButton.setLoc(28 - this._xPad, 73 - this._yPad);
        this._rightButton.setLoc(116 - this._xPad, 73 - this._yPad);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this._meatButton.setSize(24, 24);
        this._meatButton.setLocX(45 - this._xPad);
        this._meatButton.setLocY(57 - this._yPad);
        this._fishButton.setLocX(27 - this._xPad + this._meatButton.getSizeX() / this.getScale() + 29 + this._select.getSizeX() / this.getScale());
        this._fishButton.setLocY(57 - this._yPad);
        this._fruitButton.setLocX(45 - this._xPad);
        this._fruitButton.setLocY(60 - this._yPad + this._meatButton.getSizeY() / this.getScale());
        this._vegButton.setLocX(56 - this._xPad + this._fruitButton.getSizeX() / this.getScale() + this._select.getSizeX() / this.getScale());
        this._vegButton.setLocY(60 - this._yPad + this._fishButton.getSizeY() / this.getScale());
        this._meatButton.setVisible(false);
        this._fishButton.setVisible(false);
        this._fruitButton.setVisible(false);
        this._vegButton.setVisible(false);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._meatButton, this._fishButton, this._fruitButton, this._vegButton, this._rightButton, this._backButton});
    }

    private void setupConsumableButtons(Consumable[] consumable, SpriteObj o, ArrayList<SpriteObj> obj, String name, int emptyPixels, int width, int height, double scale) {
        Consumable type = consumable[0];
        if (type != null) {
            ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, name, type, o, emptyPixels, width, height, scale);
            this._meatButton.setIcon(o.getSpriteSheet()[0]);
            this._meatButton.setName(type.getID() + "");
            this._meatButton.setVisible(true);
            obj.add(this._meatButton);
        }
        if ((type = consumable[1]) != null) {
            ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, name, type, o, emptyPixels, width, height, scale);
            this._fishButton.setIcon(o.getSpriteSheet()[0]);
            this._fishButton.setName(type.getID() + "");
            this._fishButton.setVisible(true);
            obj.add(this._fishButton);
        }
        if ((type = consumable[2]) != null) {
            ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, name, type, o, emptyPixels, width, height, scale);
            this._fruitButton.setIcon(o.getSpriteSheet()[0]);
            this._fruitButton.setName(type.getID() + "");
            this._fruitButton.setVisible(true);
            obj.add(this._fruitButton);
        }
        if ((type = consumable[3]) != null) {
            ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, name, type, o, emptyPixels, width, height, scale);
            this._vegButton.setIcon(o.getSpriteSheet()[0]);
            this._vegButton.setName(type.getID() + "");
            this._vegButton.setVisible(true);
            obj.add(this._vegButton);
        }
    }

    private int getMaxConsumablePage(Enum.Menu m) {
        int total = 0;
        int max = 0;
        double numPerPage = 4.0;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        switch (m) {
            case Food_Inventory: {
                total = digimon.getFoodOwned(true).size();
                break;
            }
            case Food_Inventory_Sell: {
                total = digimon.getSellableFood().size();
                break;
            }
            case Item_Inventory: {
                total = digimon.getItemsOwned(digimon.getNormalItems(true)).size();
                break;
            }
            case Item_Inventory_Sell: {
                total = digimon.getSellableItems().size();
                break;
            }
            case Food_Shop: {
                total = digimon.getHomeFoodShop().size();
                break;
            }
            case Item_Shop: {
                total = digimon.getHomeItemShop().size();
                break;
            }
            case EvolutionInventory: {
                digimon.getItemsOwned(digimon.getEvolItems(true)).size();
                numPerPage = 1.0;
            }
        }
        return max += (int)Math.ceil((double)total / numPerPage) - 1;
    }

    private int getMaxConsumablePage(boolean isShop, boolean isEvol, Class<?> consumableType) {
        int total = 0;
        int max = 0;
        switch (consumableType.getName()) {
            case "Model.FoodType": {
                total = isShop ? this._controller.getModel().getDigimon().getHomeFoodShop().size() : this._controller.getModel().getDigimon().getFoodOwned(true).size();
                break;
            }
            case "Model.Item": {
                total = isShop ? this._controller.getModel().getDigimon().getHomeItemShop().size() : this._controller.getModel().getDigimon().getItemsOwned(isEvol ? this._controller.getModel().getDigimon().getEvolItems(true) : this._controller.getModel().getDigimon().getNormalItems(true)).size();
            }
        }
        return max += (int)Math.ceil((double)total / (isEvol ? 1.0 : 4.0)) - 1;
    }

    private void drawUseFood() {
        this.drawFoodDetail();
    }

    private void drawUseItem() {
        this.drawItemDetail();
    }

    private void drawBuyItem() {
        this.drawItemDetail();
    }

    private void drawSellItem() {
        this.drawItemDetail();
    }

    private void drawItemDetail() {
        switch (this._controller.getCurrentMenu()) {
            case UseEvolutionItem: {
                this._digisoulButton.setIsEnabled(true);
                break;
            }
            case Use_Med_Item: {
                this._firstAidButton.setIsEnabled(true);
                break;
            }
            default: {
                this._statusButton.setIsEnabled(true);
            }
        }
        this.drawConsumableDetail(this._itemType, this._controller.getCurrentMenu(), this._itemLabel, "Items", 1, 16, 16, this.getScale() * 3);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton, this._meatButton});
    }

    private void drawSellFood() {
        this.drawFoodDetail();
    }

    private void drawBuyFood() {
        this.drawFoodDetail();
    }

    private void drawFoodDetail() {
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        if (this._controller.getCurrentMenu() == Enum.Menu.Use_Med_Food) {
            this._firstAidButton.setIsEnabled(true);
        } else {
            this._feedButton.setIsEnabled(true);
        }
        this.drawConsumableDetail(this._foodType, this._controller.getCurrentMenu(), this._foodLabel, "Food", 6, 24, 24, this.getScale());
        obj.add(this._backButton);
        if (!this._foodType.getType().contains((Object)Enum.Food.None)) {
            this._optionButton.setSize(17, 12);
            this._optionButton.setLoc(this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale() - 3, this._mainInteract.getHeight() / this.getScale() - this._optionButton.getSizeY() / this.getScale() - 3);
            this._optionButton.setAltIcon("tNutrition");
            this._optionButton.setVisible(true);
            obj.add(this._optionButton);
        }
        obj.add(this._meatButton);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawConsumableDetail(Consumable c, Enum.Menu m, SpriteObj o, String name, int emptyPixels, int width, int height, int scale) {
        this._backButton.setVisible(true);
        ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, name, c, o, emptyPixels, width, height, scale);
        this._meatButton.setSize(24, 24);
        this._meatButton.setLocX(106 - this._xPad);
        this._meatButton.setLocY(54 - this._yPad);
        this._meatButton.setIcon(o.getSpriteSheet()[0]);
        this._meatButton.setVisible(true);
        int dWidth = 80 * this.getScale();
        int nameWidth = 44 * this.getScale();
        int marginName = 0 * this.getScale();
        int marginDescription = 0 * this.getScale();
        int margin = 6 * this.getScale();
        String quantity = "";
        String sale = "";
        if (m.toString().contains("Buy")) {
            if (this._consumableType != null) {
                if (this._consumableType.getCurrentStock() > -1) {
                    quantity = "Stock: " + this._consumableType.getCurrentStock() + "&nbsp;";
                }
                sale = this._consumableType.isSale() ? "Sale: " : "Price: ";
                sale = sale + this._consumableType.getPurchasePrice();
            }
        } else {
            quantity = (m.toString().contains("Food") ? "Owned: " : "Uses: ") + c.getCurrentUses();
            if (m.toString().contains("Sell")) {
                quantity = "Owned: " + c.getCurrentUses() / c.getUsesPerConsumable();
                sale = " Sell: ";
                sale = sale + this._consumableType.getResellPrice();
            } else {
                sale = "";
            }
            if (!c.getCanDecUses()) {
                quantity = "";
            }
        }
        quantity = "</p><p>" + quantity;
        this.drawConsumableDescription(c.getName(), c.getDescription() + quantity + sale);
    }

    private void drawConsumableDescription(String name, String description) {
        int dWidth = 80 * this.getScale();
        int nameWidth = 80 * this.getScale();
        int marginName = 6 * this.getScale();
        int marginDescription = 0 * this.getScale();
        int margin = 6 * this.getScale();
        this.drawConsumableDescription(name, description, dWidth, nameWidth, marginName, marginDescription, margin, 0, 0, dWidth);
    }

    private void drawConsumableDescriptionMargin(String name, String description, int margin) {
        int dWidth = 80 * this.getScale();
        int nameWidth = 80 * this.getScale();
        int marginName = 6 * this.getScale();
        int marginDescription = 0 * this.getScale();
        this.drawConsumableDescription(name, description, dWidth, nameWidth, marginName, marginDescription, margin * this.getScale(), 0, 0, dWidth);
    }

    private void drawConsumableDescription(String name, String description, int dWidth, int nameWidth, int marginName, int marginDescription, int margin, int nameSize, int descriptionSize, int descriptionWidth) {
        String ns = nameSize > 0 ? "font-size:" + nameSize + "px;" : "";
        String ds = descriptionSize > 0 ? "font-size:" + descriptionSize + "px;" : "";
        this._consumableDescription.setText("<html><div style=\"width:" + dWidth + "px;margin-top:" + margin + "px;\"><p style=\"text-align:center;font-weight:bold;" + ns + "width:" + nameWidth + "px;margin-right:" + marginName + "px;\">" + name + "</p><p style=\"width:" + descriptionWidth + "px;margin-top:" + marginDescription + "px;" + ds + "\">" + description + "</p></div></html>");
        this._consumableDescription.setVisible(true);
    }

    private void drawDNADetail(Enum.Field f) {
        this._digisoulButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._enterButton.setSizeX(18);
        this._enterButton.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._enterButton.getSizeX() / this.getScale() + 1, 1);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setVisible(true);
        this._bitsPanel.setText("01");
        this._bitsPanel.setSizeY(ViewConfig._fontSize);
        this._bitsPanel.setLocX(this._mainDisplay.getWidth() / this.getScale() / 2 - 3);
        this._bitsPanel.setLocY(-4);
        this._bitsPanel.setVisible(true);
        this._fieldLabel.setRawLoc(25 * this.getScale(), -5 * this.getScale());
        this._fieldLabel.setIcon(ViewUtil.resizeImage(this._fieldLabel.getIcon(), 0.5));
        this._fieldLabel.setVisible(true);
        this._leftButton.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - 29, this._bitsPanel.getLocY() / this.getScale() + 1);
        this._leftButton.setAltIcon("tSmall");
        this._leftButton.setVisible(true);
        this._rightButton.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 + 17, this._leftButton.getLocY() / this.getScale());
        this._rightButton.setAltIcon("tSmall");
        this._rightButton.setVisible(true);
        DNA dna = this._controller.getModel().getDigimon().getDNA();
        this.drawConsumableDescription("<br>DNA Charge", "Increases evolution priority. Chance of illness.</p><p>Owned: " + dna.getOwned(f));
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._rightButton, this._enterButton, this._backButton});
    }

    public int getPurchaseAmount() {
        return Integer.parseInt(this._stepsPanel.getText().split(" ")[1]);
    }

    public boolean changePurchaseAmount(boolean inc, String operation) {
        int i = this.getPurchaseAmount();
        String s = "x ";
        int max = 99;
        boolean canBuy = true;
        int stock = this._consumableType.getCurrentStock();
        int price = this._consumableType.getPurchasePrice();
        switch (this._controller.getCurrentMenu()) {
            case Food_Purchase: {
                canBuy = this._foodType.canIncQuantity(i + 1);
                max = this._foodType.getMaxUses() - this._foodType.getCurrentUses();
                max /= this._foodType.getUsesPerConsumable();
                break;
            }
            case Item_Purchase: {
                canBuy = this._itemType.canIncQuantity(i + 1);
                max = this._itemType.getMaxUses() - this._itemType.getCurrentUses();
                max /= this._itemType.getUsesPerConsumable();
                break;
            }
            case Food_Sale: {
                stock = this._foodType.getCurrentUses() / this._foodType.getUsesPerConsumable();
                canBuy = this._foodType.getCurrentUses() > 0;
                max = stock;
                price = this._consumableType.getResellPrice();
                break;
            }
            case Item_Sale: {
                stock = this._itemType.getCurrentUses() / this._itemType.getUsesPerConsumable();
                canBuy = this._itemType.getCurrentUses() > 0;
                max = stock;
                price = this._consumableType.getResellPrice();
            }
        }
        if (stock > -1 && max > stock) {
            max = stock;
        }
        if (inc && canBuy && (stock == -1 || stock >= i + 1)) {
            this._stepsPanel.setText(s + this.getExtraZero(++i + ""));
            this.drawPurchaseScreen(price * i, operation);
            return true;
        }
        if (!inc && i > 1) {
            this._stepsPanel.setText(s + this.getExtraZero(--i + ""));
            this.drawPurchaseScreen(price * i, operation);
            return true;
        }
        if (inc && i != 1) {
            i = 1;
            this._stepsPanel.setText(s + this.getExtraZero(i + ""));
            this.drawPurchaseScreen(price * i, operation);
            return true;
        }
        if (!inc && i < max) {
            i = max;
            this._stepsPanel.setText(s + this.getExtraZero(i + ""));
            this.drawPurchaseScreen(price * i, operation);
            return true;
        }
        return false;
    }

    private void drawPurchaseValidation(int price, String operation) {
        this._backButton.setVisible(true);
        this._enterButton.setSizeX(18);
        this._enterButton.setLoc(107 - this._xPad, 56 - this._yPad);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setVisible(true);
        this.drawPurchaseScreen(price, operation);
        this._bitsPanel.setVisible(true);
        this._bitsLabel.setVisible(true);
        this._stepsPanel.setText("x 01");
        this._stepsPanel.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - 23, -15);
        this._stepsPanel.setVisible(true);
        this._leftButton.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - 32, -3);
        this._leftButton.setAltIcon("tSmall");
        this._leftButton.setVisible(true);
        this._rightButton.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 + 16, -3);
        this._rightButton.setAltIcon("tSmall");
        this._rightButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton, this._leftButton, this._rightButton, this._enterButton});
    }

    private void drawFoodPurchase(int price) {
        this._feedButton.setIsEnabled(true);
        this.drawPurchaseValidation(price, "-");
    }

    private void drawFoodSale(int price) {
        this._feedButton.setIsEnabled(true);
        this.drawPurchaseValidation(price, "+");
    }

    private void drawItemPurchase(int price) {
        this._statusButton.setIsEnabled(true);
        this.drawPurchaseValidation(price, "-");
    }

    private void drawItemSale(int price) {
        this._statusButton.setIsEnabled(true);
        this.drawPurchaseValidation(price, "+");
    }

    private void drawHabitatPurchase(int price) {
        this._backgroundAnim.checkBackNoAnim(this._controller.getModel().getDigimon(), this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        this._statusButton.setIsEnabled(true);
        this.drawPurchaseValidation(price, "-");
    }

    private void drawPurchaseScreen(int price, String operation) {
        String bits = this.getBitsAsString(this._controller.getModel().getDigimon().getBits());
        String priceS = this.getBitsAsString(price);
        priceS = operation + " " + priceS;
        this._bitsPanel.setText("<html><div><p>" + bits + "</p><p>" + priceS + "</p></div></html>");
        this._bitsLabel.setRawLoc(3 * this.getScale(), 16 * this.getScale());
        this._bitsPanel.setSizeY(ViewConfig._fontSize * 2);
        this._bitsPanel.setLocY(62 - this._yPad);
        this._bitsPanel.setLocX(this._bitsLabel.getLocX() / this.getScale() + 26);
    }

    private void drawMedical() {
        this._backButton.setVisible(true);
        this._firstAidButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        this._meatButton.setSize(24, 24);
        this._meatButton.setLocX(48 - this._xPad);
        this._meatButton.setLocY(57 - this._yPad);
        this._fishButton.setLocX(27 - this._xPad + this._meatButton.getSizeX() / this.getScale() + 32 + this._select.getSizeX() / this.getScale());
        this._fishButton.setLocY(57 - this._yPad);
        this._fruitButton.setLocX(this._meatButton.getLocX() / this.getScale() + this._meatButton.getSizeX() / this.getScale() / 2 + 5);
        this._fruitButton.setLocY(60 - this._yPad + this._meatButton.getSizeY() / this.getScale());
        this._foodType = digimon.getFoodByID(5);
        this.setFoodSet();
        this._fruitButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
        this._fruitButton.setName(this._foodType.getID() + "");
        this._fruitButton.setVisible(true);
        this._foodType = digimon.getFoodByID(4);
        this.setFoodSet();
        this._fishButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
        this._fishButton.setName(this._foodType.getID() + "");
        this._fishButton.setVisible(true);
        this._itemType = digimon.getItemByID(80);
        this.setItemSet();
        this._meatButton.setIcon(this._itemLabel.getSpriteSheet()[0]);
        this._meatButton.setName(this._itemType.getID() + "");
        this._meatButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._meatButton, this._fishButton, this._fruitButton, this._backButton});
    }

    private void drawBattleMenu() {
        this._select.setAltIcon("select");
        this._battleButton.setIsEnabled(true);
        this._battleOption.setText("VS");
        this._battleOption.setLocX(68 - this._xPad);
        this._battleOption.setLocY(58 - this._yPad);
        this._cardsOption.setText("Cards");
        this._cardsOption.setLocX(56 - this._xPad);
        this._cardsOption.setLocY(74 - this._yPad);
        this._jogressOption.setText("Jogress");
        this._jogressOption.setSizeX(78);
        this._jogressOption.setLocX(45 - this._xPad);
        this._jogressOption.setLocY(89 - this._yPad);
        this._optionButton.setSize(14, 14);
        this._optionButton.setLoc(this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale() - 3, -1 + this._battleOption.getLocY() / this.getScale());
        this._optionButton.setAltIcon("tOption");
        this._optionButton.setVisible(true);
        this._battleOption.setVisible(true);
        this._cardsOption.setVisible(true);
        this._jogressOption.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._battleOption, this._cardsOption, this._jogressOption, this._optionButton, this._backButton});
    }

    private void drawEvolutionMenu() {
        this._select.setAltIcon("select");
        this._digisoulButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._jogressOption.setText("Digicore");
        this._jogressOption.setSizeX(70);
        this._jogressOption.setLocX(48 - this._xPad);
        this._jogressOption.setLocY(53 - this._yPad);
        this._cardsOption.setText("Items");
        this._cardsOption.setLocX(56 - this._xPad);
        this._cardsOption.setLocY(76 - this._yPad);
        this._battleOption.setText("DNA");
        this._battleOption.setLocX(62 - this._xPad);
        this._battleOption.setLocY(96 - this._yPad);
        this._digisoulButton.setVisible(true);
        this._battleOption.setVisible(true);
        this._cardsOption.setVisible(true);
        this._jogressOption.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._jogressOption, this._cardsOption, this._battleOption, this._backButton});
    }

    public void drawEvolutionInventory() {
        this._keyboard.setCursorPosition(-1);
        this._digisoulButton.setIsEnabled(true);
        this._digisoulButton.setVisible(true);
        this.setupList();
        ArrayList<Item> digimentals = this._controller.getModel().getDigimon().getItemsOwned(this._controller.getModel().getDigimon().getEvolItems(true));
        if (!digimentals.isEmpty()) {
            int i = this._consumablePage;
            Item type = digimentals.get(i);
            ViewUtil.setConsumableSet(this.MOD_FOLDER, this.RESOURCES_FOLDER, "Items", type, this._itemLabel, 1, 16, 16, this.getScale() * 3);
            this._meatButton.setName(type.getID() + "");
            this._meatButton.setIcon(this._itemLabel.getSpriteSheet()[1]);
            this._meatButton.setLocX(54 - this._xPad);
            this._meatButton.setLocY(62 - this._yPad);
            this._meatButton.setSize(48, 48);
            this._meatButton.setVisible(true);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._meatButton, this._rightButton, this._leftButton, this._backButton});
        } else {
            this._consumableDescription.setText("<html><p style=\"text-align:center;width:" + 80 * this.getScale() + "px;font-size:" + 24 * this.getScale() + "px;font-weight:bold;\">Empty</p></html>");
            this._consumableDescription.setVisible(true);
            this._rightButton.setVisible(false);
            this._leftButton.setVisible(false);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
        }
    }

    private void setupDigicore(PhysicalState digimon) {
        String[] info = this.getDigicoreConfig(digimon);
        int baseRate = Config._digicoreBaseRate;
        if (digimon.getLapsedLife() < digimon.getGrowthPeriod() && digimon.getEvolution().getNormalEvolutionCount(digimon.getIndex()) > 0) {
            double denom = Math.round((double)digimon.getGrowthPeriod() / (double)baseRate);
            if (denom == 0.0) {
                denom = 1.0;
            }
            baseRate = (int)((double)baseRate - (double)digimon.getLapsedLife() / denom);
        } else {
            double denom = Math.round((double)digimon.getTotalLifespan() / (double)baseRate);
            if (denom == 0.0) {
                denom = 1.0;
            }
            baseRate = (int)((double)digimon.getLapsedLife() / denom);
        }
        if (baseRate <= 0) {
            baseRate = 1;
        }
        this._digicore.setName(baseRate + "");
        if (digimon.getXAntibodyState() != Enum.XAntibodyState.None) {
            if (info.length > 2 && info[2] != null && !info[2].equals("")) {
                if (info[2].equals("null")) {
                    this._digicore.setVisible(false);
                } else {
                    this._digicore.setIcon(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, info[2], (double)this.getScale() * 1.5));
                }
            } else {
                switch (this._controller.getModel().getDigimon().getXAntibodyState()) {
                    case Permanent: 
                    case XProgram: {
                        this._digicore.setAltIcon("xAntibodyReq");
                        break;
                    }
                    case Temporary: {
                        this._digicore.setAltIcon("xAntibodyTemp");
                    }
                }
            }
        } else if (info.length > 1 && info[1] != null && !info[1].equals("")) {
            if (info[1].equals("null")) {
                this._digicore.setVisible(false);
            } else {
                this._digicore.setIcon(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, info[1], (double)this.getScale() * 1.5));
            }
        } else {
            this._digicore.setAltIcon("xAntibodyNoReq");
        }
        this._digicore.setVisible(true);
        this._digicore.setSize(56, 56);
        this._digicore.setLoc(31, 2);
    }

    private void drawEvolutionState(PhysicalState digimon) {
        this._backButton.setVisible(true);
        this._digisoulButton.setIsEnabled(true);
        this._digisoulButton.setVisible(true);
        this.setupDigicore(digimon);
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        if (digimon.canModeChange()) {
            this._optionButton.setSize(20, 20);
            this._optionButton.setLoc(-1 + this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale(), -3 + this._battleOption.getLocY() / this.getScale());
            this._optionButton.setAltIcon("tModeChange");
            this._optionButton.setVisible(true);
            obj.add(this._optionButton);
        }
        obj.add(this._backButton);
        obj.add(this._digicore);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void evolSilhouetteTransition() {
        this.fade(this._interval * 6);
        if (this._frame <= 0) {
            this._digicore.setVisible(true);
            this._character.setVisible(false);
            this._frame = 0;
        } else if (this._frame == this._interval * 2) {
            this._sounds.playSound(SoundConfig._digicorePulse);
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) / 1.5));
            this._digicore.moveRight(6);
            this._digicore.moveDown(2);
        } else if (this._frame == this._interval * 3) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(2);
            this._digicore.moveLeft(6);
        } else if (this._frame == this._interval * 4) {
            this._sounds.playSound(SoundConfig._digicorePulse);
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) / 1.5));
            this._digicore.moveRight(6);
            this._digicore.moveDown(2);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._digicoreExpand);
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(2);
            this._digicore.moveLeft(6);
        } else if (this._frame == this._interval * 7) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 8) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 9) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 10) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 11) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 12) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 13) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
        } else if (this._frame == this._interval * 14) {
            this._digicore.setIcon(ViewUtil.resizeImage(this._digicore.getIcon(), (double)(this.getScale() / this.getScale()) * 1.5));
            this._digicore.moveUp(this._digicore.getSizeY() / this.getScale() / 4);
            this._digicore.moveLeft(this._digicore.getSizeX() / this.getScale() / 5);
            this._digicore.setSize(this._digicore.getSizeX() / this.getScale() + this._digicore.getSizeX() / this.getScale() / 2, this._digicore.getSizeY() / this.getScale() + this._digicore.getSizeY() / this.getScale() / 2);
            this._background.setSize(ViewConfig._habitatDimensions[0] + ViewConfig._habitatDimensions[0] / 2, ViewConfig._habitatDimensions[1] + ViewConfig._habitatDimensions[1] / 2);
            this._background.setLoc(-30, -40);
            this._background.setIcon(ViewUtil.resizeImage(this._background.getIcon(), 2.0));
            this._digicore.setVisible(false);
            PhysicalState digimon = this._controller.getModel().getDigimon();
            ArrayList<EvolutionInfo> evolutions = digimon.getEvolution().getCurrentNaturalEvol(digimon);
            if (evolutions != null) {
                this.drawSilhouette(evolutions, 0);
            } else {
                this.setEvolvingIcon(0);
            }
            this._opponent.setLocX(55 - this._xPad);
            this._opponent.setLocY(63 - this._yPad);
            this._opponent.setSize(48, 48);
        } else if (this._frame == this._interval * 24) {
            this.endAnim();
            this.drawEvolSilhouette();
            this._controller.setCurrentMenu(Enum.Menu.EvolSilhouette);
            this.checkMenuAnims(Enum.Menu.EvolSilhouette, this._controller.getModel().getDigimon());
        }
    }

    private void evolSilhouetteBack(PhysicalState digimon) {
        this.fade(this._interval * 0);
        this._character.setVisible(false);
        if (this._frame <= 0) {
            this._sounds.playSound(SoundConfig._silhouetteFade);
            this._opponent.setVisible(true);
            this._frame = 0;
        } else if (this._frame == 8 * this._interval) {
            this._opponent.setVisible(false);
            this.setupDigicore(digimon);
            this._backgroundAnim.checkBackNoAnim(digimon, Enum.Menu.EvolutionState, this.getScale(), this._controller.getBattle());
        } else if (this._frame == 18 * this._interval) {
            this.endAnim();
            this._controller.setCurrentMenu(Enum.Menu.EvolutionState);
        }
    }

    private void drawSilhouette(ArrayList<EvolutionInfo> evolutions, int evol) {
        if (evolutions != null) {
            EvolutionInfo e;
            if (evol < 0) {
                evol = 0;
            }
            if ((e = evolutions.get(evol)) != null) {
                Icon evo = this.getIndividualIcon(e.getNewStage(), e.getNewSpriteSet(), this.getScale(), e.getNewSpriteNum(), 0, 48, 48, 12);
                Icon i = ViewUtil.resizeImage(evo, (double)(this.getScale() / this.getScale()) / 3.0);
                i = ViewUtil.getSilhouetteImage(i);
                this._opponent.setIcon(ViewUtil.resizeImage(i, (double)(this.getScale() / this.getScale()) * 3.0));
                this._opponent.setVisible(true);
            }
        }
    }

    private void drawEvolSilhouette() {
        this._backButton.setVisible(true);
        this._opponent.setVisible(true);
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        obj.add(this._backButton);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawDNAMenu() {
        this._consumablePage = 0;
        this._digisoulButton.setIsEnabled(true);
        this._select.setAltIcon("select");
        this._battleOption.setText("DNA");
        this._battleOption.setLocX(62 - this._xPad);
        this._battleOption.setLocY(58 - this._yPad);
        this._cardsOption.setText("Charge");
        this._cardsOption.setLocX(50 - this._xPad);
        this._cardsOption.setLocY(75 - this._yPad);
        this._jogressOption.setText("Generate");
        this._jogressOption.setSizeX(78);
        this._jogressOption.setLocX(42 - this._xPad);
        this._jogressOption.setLocY(91 - this._yPad);
        this._battleOption.setVisible(true);
        this._cardsOption.setVisible(true);
        this._jogressOption.setVisible(true);
        this._digisoulButton.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._battleOption, this._cardsOption, this._jogressOption, this._optionButton, this._backButton});
    }

    public void drawDNAStats() {
        this._backButton.setVisible(true);
        this._digisoulButton.setVisible(true);
        this._digisoulButton.setIsEnabled(true);
        this.drawDNAList();
        Enum.Field f = Enum.Field.values()[this._consumablePage];
        int fieldAmount = this._controller.getModel().getDigimon().getDNA().getPercent(f);
        this.setDNADisplay(fieldAmount + "%");
        this._keyboard.setCursorPosition(-1);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._rightButton, this._leftButton, this._backButton});
    }

    public void drawDNACharge() {
        this._backButton.setVisible(true);
        this._digisoulButton.setVisible(true);
        this._digisoulButton.setIsEnabled(true);
        this.drawDNAList();
        Enum.Field f = Enum.Field.values()[this._consumablePage];
        int fieldAmount = this._controller.getModel().getDigimon().getDNA().getOwned(f);
        this.setDNADisplay("x" + fieldAmount);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._fieldLabel, this._rightButton, this._leftButton, this._backButton});
    }

    private void drawDNAGenerateValidate() {
        this._backButton.setVisible(true);
        this._digisoulButton.setIsEnabled(true);
        this._enterButton.setSizeX(18);
        this._enterButton.setLoc(111 - this._xPad, 98 - this._yPad);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setVisible(true);
        this._roomEffect.setAltIcon("dnaGenerateValidation");
        this._roomEffect.setVisible(true);
        this._bitsPanel.setText("01");
        ViewUtil.centerObj(this._mainDisplay, this._bitsPanel);
        this._bitsPanel.setLocX(this._mainDisplay.getWidth() / this.getScale() / 2 - 14);
        this._bitsPanel.moveDown(2);
        this._bitsPanel.setVisible(true);
        this._leftButton.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - 22, 19);
        this._leftButton.setAltIcon("tSmall");
        this._leftButton.setVisible(true);
        this._rightButton.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 + 6, this._leftButton.getLocY() / this.getScale());
        this._rightButton.setAltIcon("tSmall");
        this._rightButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._rightButton, this._enterButton, this._backButton});
    }

    public void changeDNAChargeQuantity(boolean add, DNA dna) {
        this.changeDNAQuantity(add, dna.getOwned(Enum.Field.values()[this._consumablePage]));
    }

    public void changeDNAQuantity(boolean add, int max) {
        int amount = Integer.parseInt(this._bitsPanel.getText());
        if (add) {
            if (++amount > max) {
                amount = 1;
            }
        } else if (--amount <= 0) {
            amount = max;
        }
        this._bitsPanel.setText(this.getExtraZero(Integer.toString(amount)));
    }

    public int getDNAAmount() {
        return Integer.parseInt(this._bitsPanel.getText());
    }

    public void drawDNAGenerate() {
        this._menuRect.setVisible(true);
        this._controller.setNumHits(0);
        this._fieldLabel.setLoc(4, 1);
        this._fieldLabel.setAltIcon("bits");
        this._hitButton.setLoc(45, 10);
        this._rateLabel.setSizeX(0);
        this._rateLabel.setLoc(2, 29);
        this._rate.setLoc(2, 28);
        this._rate.setVisible(true);
        this._rateLabel.setVisible(true);
        this._hitButton.setVisible(true);
        this._fieldLabel.setVisible(true);
        try {
            Robot r = new Robot();
            r.mouseMove(this._hitButton.getLocationOnScreen().x + this._hitButton.getSizeX() / 2, this._hitButton.getLocationOnScreen().y + this._hitButton.getSizeY() / 4);
        }
        catch (AWTException ex) {
            Logger.getLogger(SpriteAnim.class.getName()).log(Level.SEVERE, null, ex);
        }
        catch (IllegalComponentStateException illegalComponentStateException) {
            // empty catch block
        }
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._hitButton});
    }

    private void setDNADisplay(String amount) {
        this._weightPanel.setBounds(this._mainDisplay.getWidth() / 2 - 17 * this.getScale(), this._fieldLabel.getLocY() + this._fieldLabel.getSizeY() - 2, 60 * this.getScale(), 30 * this.getScale());
        String pad = "";
        if (amount.length() == 2) {
            pad = "  ";
        } else if (amount.length() == 3) {
            pad = " ";
        }
        this._weightPanel.setText(pad + amount);
        this._weightPanel.setVisible(true);
    }

    private void drawDNAList() {
        this._leftButton.setLoc(28 - this._xPad, 73 - this._yPad);
        this._rightButton.setLoc(116 - this._xPad, 73 - this._yPad);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        Enum.Field f = Enum.Field.values()[this._consumablePage];
        this.checkField(f);
        this._fieldLabel.setLoc(this._mainDisplay.getWidth() / this.getScale() / 4 - this._fieldLabel.getSizeX() / this.getScale() / 4, 3);
        this._fieldLabel.setVisible(true);
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
    }

    public void drawBattleStyleMenu() {
        this._backButton.setVisible(true);
        this._battleButton.setIsEnabled(true);
        this._surrenderOption.setText("Style");
        this._surrenderOption.removeIcon();
        this._surrenderOption.setLoc(33, 3);
        this._surrenderOption.setSize(100, 21);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (digimon.getIsFree()) {
            this._yesLabel.setText("Free");
            this._yesLabel.setLocX(61 - this._xPad);
            this._yesLabel.setSizeX(48);
        } else {
            this._yesLabel.setText("Orders");
            this._yesLabel.setSizeX(60);
            this._yesLabel.setLocX(53 - this._xPad);
        }
        this._yesLabel.setLocY(this._surrenderOption.getLocY() / this.getScale() + 25);
        this._yesLabel.setVisible(true);
        this._surrenderOption.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._backButton});
    }

    private void drawTourneyMenu() {
        this._battleButton.setIsEnabled(true);
        this._tourneyRecords.setVisible(true);
        this._tourneyEnter.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._tourneyRecords, this._tourneyEnter, this._backButton});
    }

    private void drawRecordsSelectMenu() {
        this._battleButton.setIsEnabled(true);
        this._seasonRecords.setVisible(true);
        this._springRecords.setAltIcon("tSpring");
        this._springRecords.setLoc(53 - this._xPad, 58 - this._yPad);
        this._springRecords.setVisible(true);
        this._summerRecords.setLoc(83 - this._xPad, 58 - this._yPad);
        this._summerRecords.setAltIcon("tSummer");
        this._summerRecords.setVisible(true);
        this._fallRecords.setAltIcon("tFall");
        this._fallRecords.setLoc(53 - this._xPad, 88 - this._yPad);
        this._fallRecords.setVisible(true);
        this._winterRecords.setAltIcon("tWinter");
        this._winterRecords.setLoc(83 - this._xPad, 88 - this._yPad);
        this._winterRecords.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._springRecords, this._summerRecords, this._fallRecords, this._winterRecords, this._backButton});
    }

    private void resetTrophies() {
        this.resetScreen();
        this._trophies[0].setLoc(49 - this._xPad, 60 - this._yPad);
        this._trophies[1].setLoc(69 - this._xPad, 60 - this._yPad);
        this._trophies[2].setLoc(89 - this._xPad, 60 - this._yPad);
        this._trophies[3].setLoc(49 - this._xPad, 80 - this._yPad);
        this._trophies[4].setLoc(69 - this._xPad, 80 - this._yPad);
        this._trophies[5].setLoc(89 - this._xPad, 80 - this._yPad);
        for (SpriteObj t : this._trophies) {
            t.setSize(18, 18);
            t.setScale(this.getScale());
        }
    }

    public void drawRecordsMenu(Enum.Season s) {
        this.resetTrophies();
        this._battleButton.setIsEnabled(true);
        this._leftButton.setLoc(28 - this._xPad, 73 - this._yPad);
        this._rightButton.setLoc(116 - this._xPad, 73 - this._yPad);
        Tournament tourney = this._controller.getModel().getDigimon().getTournament();
        int index = 0;
        int max = 0;
        for (SpriteObj t : this._trophies) {
            Trophy trophy = null;
            try {
                switch (s) {
                    case Spring: {
                        trophy = tourney.getSpringTrophies().get(index + this._trophyPage * ViewConfig._trophyRecordsPageSize);
                        max = tourney.getSpringTrophies().size();
                        break;
                    }
                    case Summer: {
                        trophy = tourney.getSummerTrophies().get(index + this._trophyPage * ViewConfig._trophyRecordsPageSize);
                        max = tourney.getSummerTrophies().size();
                        break;
                    }
                    case Fall: {
                        trophy = tourney.getFallTrophies().get(index + this._trophyPage * ViewConfig._trophyRecordsPageSize);
                        max = tourney.getFallTrophies().size();
                        break;
                    }
                    case Winter: {
                        trophy = tourney.getWinterTrophies().get(index + this._trophyPage * ViewConfig._trophyRecordsPageSize);
                        max = tourney.getWinterTrophies().size();
                        break;
                    }
                    case None: {
                        break;
                    }
                    default: {
                        throw new AssertionError((Object)s.name());
                    }
                }
            }
            catch (IndexOutOfBoundsException indexOutOfBoundsException) {
                // empty catch block
            }
            if (trophy != null && trophy.getEarned()) {
                Icon i = this.getTrophySprite(trophy, (byte)(this.getScale() * 2));
                if (!trophy.getSeasonBeat()) {
                    i = ViewUtil.getTransparentImage(i, 0.5f);
                }
                t.setIcon(i);
                t.setVisible(true);
            } else if (trophy == null) {
                t.setVisible(false);
            } else {
                trophy = new Trophy();
                t.setIcon(this.getTrophySprite(trophy, (byte)(this.getScale() * 2)));
                t.setVisible(true);
            }
            ++index;
        }
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this._backButton.setVisible(true);
        ArrayList<SpriteObj> sprites = new ArrayList<SpriteObj>();
        sprites.add(this._leftButton);
        for (SpriteObj t : this._trophies) {
            sprites.add(t);
        }
        sprites.add(this._rightButton);
        sprites.add(this._backButton);
        Component[] array = new SpriteObj[sprites.size()];
        for (int i = 0; i < array.length; ++i) {
            array[i] = (SpriteObj)sprites.get(i);
        }
        int size = (int)Math.ceil((double)max / (double)ViewConfig._trophyRecordsPageSize);
        this._currentTemp.setText("<html><p style=\"text-align:center;font-size:" + 18 * this.getScale() + "px;\">" + (this._trophyPage + 1) + "/" + size + "</p></html>");
        int x = this._mainDisplay.getWidth() / 2 - this._currentTemp.getPreferredSize().width / 2;
        this._currentTemp.setLocX(x / this.getScale());
        this._currentTemp.setVisible(true);
        this._keyboard.addInteractiveButtons(array);
    }

    private void drawTrophyPrizeBits(PhysicalState digimon) {
        this._battleButton.setIsEnabled(true);
        Trophy t = this.getCurrentSelectedTrophy(digimon);
        this._backButton.setVisible(true);
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        obj.add(this._backButton);
        if (t.getFood()[0] != -1 || t.getItem() != -1) {
            this._enterButton.setSizeX(18);
            this._enterButton.setLoc(107 - this._xPad, 56 - this._yPad);
            this._enterButton.setAltIcon("enterButton");
            this._enterButton.setVisible(true);
            obj.add(this._enterButton);
        }
        int[] range = t.getMinMaxBits(digimon);
        int min = range[0];
        int max = range[1];
        String first = "";
        String second = "";
        String third = "";
        if (min != 0) {
            first = min + " - ";
            second = min / 2 + " - ";
            third = min / 3 + " - ";
        }
        first = first + max;
        second = second + max / 2;
        third = third + max / 3;
        this._consumableDescription.setText("<html><p style=\"text-align:center;font-weight:bold;font-size:" + 16 * this.getScale() + "px;\">Prizes</p><p style=\"text-align:center;width:" + 80 * this.getScale() + "px;font-size:" + 16 * this.getScale() + "px;\">1st: " + first + "<br>2nd: " + second + "<br>3rd: " + third + "</p></html>");
        this._consumableDescription.setVisible(true);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawTrophyPrizeItem() {
        this._battleButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        Trophy t = this.getCurrentSelectedTrophy(this._controller.getModel().getDigimon());
        boolean isItem = t.getItem() != -1;
        this._itemType = null;
        this._itemLabel.setLoc(56 - this._xPad, 60 - this._yPad);
        if (isItem) {
            this._itemType = this._controller.getModel().getDigimon().getItems().get(t.getItem());
            this.setItemSet();
        } else {
            this._foodType = this._controller.getModel().getDigimon().getFoodTypes().get(t.getFood()[0]);
            this.setFoodSet();
        }
        if (this._itemType != null && this._itemType.getAnim() == Enum.State.ItemEvol) {
            this._itemLabel.setIcon(this._itemLabel.getSpriteSheet()[1]);
        } else {
            this._itemLabel.setLocX(66 - this._xPad);
            this._itemLabel.moveDown(3);
            if (isItem) {
                this._itemLabel.setIcon(this._itemLabel.getSpriteSheet()[0]);
            } else {
                this._itemLabel.setIcon(this._foodLabel.getSpriteSheet()[0]);
            }
        }
        this._itemLabel.setVisible(true);
        if (!isItem && t.getFood()[1] > 1) {
            this._consumableDescription.setText("<html><p style=\"text-align:center;font-weight:bold;width:" + 80 * this.getScale() + "px;font-size:" + 16 * this.getScale() + "px;\">Prizes<br><br><br></p><p style=\"text-align:center;font-weight:bold;font-size:" + 16 * this.getScale() + "px;\">x" + t.getFood()[1] + "</p></html>");
            this._consumableDescription.setVisible(true);
        } else if (t.getFood()[1] == 1 || this._itemType != null && this._itemType.getAnim() != Enum.State.ItemEvol) {
            this._consumableDescription.setText("<html><p style=\"text-align:center;font-weight:bold;width:" + 80 * this.getScale() + "px;font-size:" + 16 * this.getScale() + "px;\">Prizes<br><br><br><br></p></html>");
            this._consumableDescription.setVisible(true);
        }
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
    }

    public void drawTrophyPrelimDetails() {
        Trophy t = this._controller.getModel().getDigimon().getTournament().getCurrentTrophy();
        SpriteObj o = null;
        switch (t.getSeason()) {
            case Summer: {
                o = this._summerRecords;
                o.setAltIcon("summer");
                break;
            }
            case Winter: {
                o = this._winterRecords;
                o.setAltIcon("winter");
                break;
            }
            case Spring: {
                o = this._springRecords;
                o.setAltIcon("spring");
                break;
            }
            case Fall: {
                o = this._fallRecords;
                o.setAltIcon("fall");
            }
        }
        o.setLoc(this._backButton.getLocX() / this.getScale() + this._backButton.getSizeX() / this.getScale() + 1, -4 + this._backButton.getLocY() / this.getScale());
        o.setVisible(true);
        this.drawTrophyDetailsMenu(true);
    }

    private void drawTrophyDetailsMenu(boolean checkTransparency) {
        this._battleButton.setIsEnabled(true);
        Trophy currentTrophy = this._controller.getModel().getDigimon().getTournament().getCurrentTrophy();
        ArrayList<JComponent> obj = new ArrayList<JComponent>();
        obj.add(this._backButton);
        this._trophies[0].setLoc(68 - this._xPad, 63 - this._yPad);
        this._trophies[0].setSize(30, 27);
        Icon i = this.getTrophySprite(currentTrophy, (byte)(this.getScale() * 3));
        if (checkTransparency && !currentTrophy.getSeasonBeat()) {
            i = ViewUtil.getTransparentImage(i, 0.5f);
        }
        this._trophies[0].setIcon(i);
        this._trophies[0].setVisible(true);
        JComponent pt = null;
        for (SpriteObj t : this._trophies) {
            if (t.getName() == null || !t.getName().equals("Prelim")) continue;
            pt = t;
            break;
        }
        if (currentTrophy.getPrelim() != 0) {
            if (pt != null) {
                obj.add(pt);
                ((SpriteObj)pt).setLoc(29 - this._xPad, 73 - this._yPad);
                ((SpriteObj)pt).setSize(18, 18);
                Trophy t = this._controller.getModel().getDigimon().getTournament().getTrophy(currentTrophy.getPrelim());
                Icon pi = this.getTrophySprite(t, (byte)(this.getScale() * 2));
                if (!t.getSeasonBeat()) {
                    pi = ViewUtil.getTransparentImage(pi, 0.5f);
                }
                ((JLabel)pt).setIcon(pi);
                pt.setVisible(true);
            }
        } else if (pt != null) {
            pt.setVisible(false);
        }
        if (currentTrophy.getFieldRestriction() != Enum.Field.NA) {
            this._fieldLabel.setLocX(50 - this._xPad / 2);
            this._fieldLabel.setLocY(28 - this._yPad / 2);
            this.checkField(currentTrophy.getFieldRestriction());
            this._fieldLabel.setVisible(true);
        }
        if (currentTrophy.getAttributeRestriction() != Enum.Attribute.NA) {
            this._attribute.setLoc(49 - this._xPad, 70 - this._yPad);
            this._attribute.setVisible(true);
            this.checkAttribute(currentTrophy.getAttributeRestriction());
            if (currentTrophy.getAttributeRestriction() == Enum.Attribute.None) {
                this._attribute.setIcon(ViewUtil.resizeImage(this._attribute.getIcon(), 0.5));
            }
        }
        if (currentTrophy.getAgeLimit() != Enum.Stage.None) {
            String age = Integer.toString(currentTrophy.getAge());
            this._agePanel.setBounds((30 - this._xPad + (age.length() < 2 ? 5 : 0)) * this.getScale(), (87 - this._yPad) * this.getScale(), 100 * this.getScale(), ViewConfig._fontSize * this.getScale());
            this._agePanel.setText("Max Age: " + age);
            this._agePanel.setVisible(true);
        } else {
            String champ = "<html><p style=\"font-size:" + 22 * this.getScale() + "px;\">Championship</p></html>";
            this._agePanel.setText(currentTrophy.getResetWon() ? champ : "No Limit");
            this._agePanel.setSize(this._agePanel.getPreferredSize().width, this._agePanel.getPreferredSize().height);
            ViewUtil.centerObj(this._mainDisplay, this._agePanel);
            this._agePanel.setLocation(this._agePanel.getX(), (92 - this._yPad) * this.getScale());
            this._agePanel.setVisible(true);
        }
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private Icon getTrophySprite(Trophy trophy, byte scale) {
        String spriteName = "trophies" + (Object)((Object)trophy.getSeason()) + trophy.getSpriteSet() + ".png";
        int w = 9;
        int h = 9;
        SpriteObj obj = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, spriteName, null, w, h, 2, scale);
        return obj.getSpriteSheet()[trophy.getSpriteNum()];
    }

    public void drawTourneySchedule() {
        this._leftButton.setLoc(26 - this._xPad, 72 - this._yPad);
        this._rightButton.setLoc(118 - this._xPad, 72 - this._yPad);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._battleButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._leftButton.setVisible(true);
        this._rightButton.setVisible(true);
        this._optionButton.setSize(15, 14);
        this._optionButton.setLoc(1 + this._backButton.getLocX() / this.getScale() + this._backButton.getSizeX() / this.getScale(), 2 + this._backButton.getLocY() / this.getScale());
        this._prizeButton.setLoc(this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale() - 3, 3);
        this._prizeButton.setAltIcon("tPrize");
        this._prizeButton.setVisible(true);
        this._trophies[0].setLoc(61 - this._xPad, 57 - this._yPad);
        this._trophies[0].setSize(36, 36);
        this.refreshTrophySchedule();
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._trophies[0], this._rightButton, this._optionButton, this._prizeButton, this._backButton});
    }

    public Trophy getCurrentSelectedTrophy(PhysicalState digimon) {
        Trophy currentTrophy = digimon.getTournament().getTrophy(digimon.getTrophySchedule()[this._trophyInSchedule]);
        return currentTrophy;
    }

    private Trophy refreshTrophySchedule() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Trophy currentTrophy = this.getCurrentSelectedTrophy(digimon);
        this._trophies[0].setIcon(this.getTrophySprite(currentTrophy, (byte)(this.getScale() * 4)));
        this._trophies[0].setVisible(true);
        int time = digimon.getTournament().getTourneyTime(this._trophyInSchedule);
        byte hour = this._controller.getModel().getTime().getHours();
        String s = (time < 10 ? "0" + time : Integer.valueOf(time)) + ":00";
        boolean closed = digimon.getTournament().checkTourneyClosed(time, hour);
        if (!closed && digimon.getFoughtTrophiesToday().contains(currentTrophy.getID())) {
            s = "CLOSED";
        } else if (closed) {
            this.checkTourneyAlarmSwitch(digimon);
        } else {
            this._optionButton.setVisible(false);
            s = time == -1 ? "OPEN" : s + " OPEN";
        }
        String registration = "<html><div style=\"width:" + 80 * this.getScale() + "px;text-align:center;\">" + s + "</div></html>";
        this._availableHours.setText(registration);
        this._availableHours.setLocY(84 - this._yPad);
        this._availableHours.setVisible(true);
        return currentTrophy;
    }

    private void drawTourneyRegistration() {
        this._enterButton.setSizeX(18);
        this._enterButton.setLoc(44 - this._xPad, 56 - this._yPad);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setVisible(true);
        this.drawTrophyDetailsMenu(false);
        this._keyboard.addButton(this._enterButton);
    }

    private void drawTourneyValidation() {
        this._okValidation.setText("Enter?");
        this._okValidation.setSize(60, 18);
        this._okValidation.setLoc(53 - this._xPad, 59 - this._yPad);
        this._okValidation.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(80 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(80 - this._yPad);
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void drawRoster() {
        this._battleButton.setIsEnabled(true);
        Tournament t = this._controller.getModel().getDigimon().getTournament();
        this._royaleNum.setText("# " + (t.getPlayerIndex() + 1));
        this._royaleNum.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - 7 - (this.getScale() > 1 ? 2 : 0) - this._royaleNum.getText().length() / this.getScale() / 2, -6);
        this._royaleNum.setVisible(true);
        this._roster.setLocX(1);
        this._roster.setLocY(16);
        this._participants[0].setLocX(this._roster.getLocX() / this.getScale() + 5);
        this._participants[0].setLocY(this._roster.getLocY() / this.getScale() + 2);
        this._participants[1].setLocX(this._roster.getLocX() / this.getScale() + 31);
        this._participants[1].setLocY(this._roster.getLocY() / this.getScale() + 2);
        this._participants[2].setLocX(this._roster.getLocX() / this.getScale() + 57);
        this._participants[2].setLocY(this._roster.getLocY() / this.getScale() + 2);
        this._participants[3].setLocX(this._roster.getLocX() / this.getScale() + 83);
        this._participants[3].setLocY(this._roster.getLocY() / this.getScale() + 2);
        this._participants[4].setLocX(this._roster.getLocX() / this.getScale() + 5);
        this._participants[4].setLocY(this._roster.getLocY() / this.getScale() + 24);
        this._participants[5].setLocX(this._roster.getLocX() / this.getScale() + 31);
        this._participants[5].setLocY(this._roster.getLocY() / this.getScale() + 24);
        this._participants[6].setLocX(this._roster.getLocX() / this.getScale() + 57);
        this._participants[6].setLocY(this._roster.getLocY() / this.getScale() + 24);
        this._participants[7].setLocX(this._roster.getLocX() / this.getScale() + 83);
        this._participants[7].setLocY(this._roster.getLocY() / this.getScale() + 24);
        this._backButton.setVisible(true);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setVisible(true);
        this._roster.setVisible(true);
        for (int i = 0; i < this._participants.length; ++i) {
            Icon icon;
            if (t.getRoster()[i] != null) {
                icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 0, 48, 48, 12);
                this._participants[i].setIcon(icon);
            } else {
                this._participants[i].setSpriteNum(0);
                this._participants[i].setSpriteSheet(this._character.getSpriteSheet());
                this._participants[i].setSpriteLoc(this._character.getSpriteLoc());
            }
            this._participants[i].setSize(16, 16);
            if (t.getDisqualified().contains(t.getRoster()[i])) {
                icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 10, 48, 48, 12);
                this._participants[i].setIcon(icon);
            } else if (t.getRoster()[i] != null) {
                icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 0, 48, 48, 12);
                this._participants[i].setIcon(icon);
            } else {
                this._participants[i].setIcon(ViewUtil.resizeImage(this._participants[i].getSpriteSheet()[this._participants[i].getSpriteNum()], (double)(this.getScale() / this.getScale()) / 3.0));
            }
            this._participants[i].setVisible(true);
        }
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._enterButton, this._backButton});
    }

    private void drawRoyaleLineup() {
        this._battleButton.setIsEnabled(true);
        this._backButton.setVisible(true);
        this._enterButton.setLoc(83, 2);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setVisible(true);
        this.setupRoyaleLineup();
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._enterButton, this._backButton});
    }

    private void setupRoyaleLineup() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Trophy currentTrophy = digimon.getTournament().getCurrentTrophy();
        this._trophies[0].setIcon(this.getTrophySprite(currentTrophy, (byte)(this.getScale() * 2)));
        this._trophies[0].setSize(18, 18);
        this._trophies[0].setLoc(43, 3);
        this._trophies[0].setVisible(true);
        this._royaleLineup.setLoc(3, 0);
        this._royaleLineup.setVisible(true);
    }

    private void drawTourneySurrender() {
        this.drawSurrenderMenu();
    }

    private void drawCardMenu() {
        this._battleButton.setIsEnabled(true);
        this._cardShop.setVisible(true);
        this._collection.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._cardShop, this._collection, this._backButton});
    }

    private void drawShopValidation() {
        this._statusButton.setIsEnabled(true);
        this._habitat = -1;
        this._backgroundAnim.checkBackNoAnim(this._controller.getModel().getDigimon(), this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        this._backButton.setVisible(true);
        this._habitatLabel.setVisible(true);
        this._itemOption.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._habitatLabel, this._itemOption, this._backButton});
    }

    private void drawInventoryValidation() {
        this._habitat = -1;
        this._backButton.setVisible(true);
        this._statusButton.setIsEnabled(true);
        this._habitatLabel.setVisible(true);
        this._itemOption.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._habitatLabel, this._itemOption, this._backButton});
    }

    private void drawConsumableList(ArrayList<Consumable> c, ArrayList<ShopConsumable> sc, SpriteObj o, String name, int emptyPixels, int width, int height, double scale) {
        this._keyboard.setCursorPosition(-1);
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        boolean isEmpty = false;
        this.setupList();
        try {
            if (sc != null) {
                int i = 4 * this._consumablePage;
                Consumable[] cb = new Consumable[4];
                for (int index = 0; index < cb.length; ++index) {
                    if (sc.size() <= i + index) continue;
                    cb[index] = sc.get(i + index).getConsumable(c);
                }
                this.setupConsumableButtons(cb, o, obj, name, emptyPixels, width, height, scale);
                if (!this._controller.getCurrentMenu().toString().contains("Sell")) {
                    this.drawSaleAlerts(this._controller.getCurrentMenu());
                }
            } else if (c != null) {
                int i = 4 * this._consumablePage;
                isEmpty = c.isEmpty();
                if (!isEmpty) {
                    Consumable[] cb = new Consumable[4];
                    for (int index = 0; index < cb.length; ++index) {
                        if (c.size() <= i + index) continue;
                        cb[index] = c.get(i + index);
                    }
                    this.setupConsumableButtons(cb, o, obj, name, emptyPixels, width, height, scale);
                } else {
                    this._consumableDescription.setText("<html><p style=\"text-align:center;width:" + 80 * this.getScale() + "px;font-size:" + 24 * this.getScale() + "px;font-weight:bold;\">Empty</p></html>");
                    this._consumableDescription.setVisible(true);
                    this._rightButton.setVisible(false);
                    this._leftButton.setVisible(false);
                }
            }
        }
        catch (IndexOutOfBoundsException indexOutOfBoundsException) {
            // empty catch block
        }
        if (!isEmpty) {
            obj.add(this._rightButton);
            obj.add(this._leftButton);
        }
        obj.add(this._backButton);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    public void drawItemShop() {
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.drawConsumableList(digimon.getItemsAsConsumable(), digimon.getHomeItemShop(), this._itemLabel, "Items", 1, 16, 16, this.getScale() * 3);
    }

    public void drawItemInventory() {
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.drawConsumableList(digimon.getItemsAsConsumable(digimon.getItemsOwned(digimon.getNormalItems(true))), null, this._itemLabel, "Items", 1, 16, 16, this.getScale() * 3);
    }

    public ArrayList<ShopConsumable> drawItemSaleInventory() {
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        ArrayList<ShopConsumable> sc = digimon.getSellableItems();
        this.drawConsumableList(digimon.getItemsAsConsumable(), sc, this._itemLabel, "Items", 1, 16, 16, this.getScale() * 3);
        return sc;
    }

    private void drawHabitatShop(Enum.Menu currentMenu, Enum.Menu lastMenu) {
        if (this.drawShop(currentMenu)) {
            this.drawHabitats(true, lastMenu);
        }
    }

    public int getCurrentFieldElement(Enum.Menu m) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        boolean c = m == Enum.Menu.Habitat_Compatibility || m == Enum.Menu.Habitat_Shop_Compatibility;
        Habitat habitat = digimon.getCurrentHabitat();
        int page = c ? this.getCompatibleFieldElementPage(digimon, habitat.getCompatibleFields(), habitat.getCompatibleElements()) : this.getCompatibleFieldElementPage(digimon, habitat.getIncompatibleFields(), habitat.getIncompatibleElements());
        return page;
    }

    private int getCompatibleFieldElementPage(PhysicalState digimon, ArrayList<Enum.Field> f, ArrayList<Enum.Element> e) {
        int i;
        int page = 0;
        for (i = 0; i < f.size(); ++i) {
            if (f.get(i) != digimon.getField()) continue;
            return i;
        }
        for (i = 0; i < e.size(); ++i) {
            if (e.get(i) != digimon.getElement()) continue;
            return i + f.size();
        }
        return page;
    }

    private void drawHabitatCompatibility(Enum.Menu m) {
        boolean isEmpty;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._frame = 0;
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
        ViewUtil.centerObj(this._mainDisplay, this._moodLabel);
        this._moodLabel.setLocX(0);
        this._moodLabel.moveRight(3);
        this._moodLabel.moveDown(12);
        this._moodLabel.setVisible(false);
        this._elementLabel.setVisible(false);
        this._fieldLabel.setVisible(false);
        this._statusButton.setIsEnabled(true);
        boolean c = m == Enum.Menu.Habitat_Compatibility || m == Enum.Menu.Habitat_Shop_Compatibility;
        this._backButton.setVisible(true);
        if (m != Enum.Menu.Habitat_Incompatibility) {
            this._enterButton.setAltIcon("enterButton");
            this._enterButton.setSizeX(18);
            this._enterButton.setLoc(107 - this._xPad, 56 - this._yPad);
            this._enterButton.setVisible(true);
        }
        Habitat habitat = this._controller.getModel().getDigimon().getHabitats().get(this._habitat);
        boolean bl = c ? habitat.getCompatibleElements().isEmpty() && habitat.getCompatibleFields().isEmpty() : (isEmpty = habitat.getIncompatibleElements().isEmpty() && habitat.getIncompatibleFields().isEmpty());
        if (!isEmpty) {
            Enum.Field f = null;
            Enum.Element e = null;
            boolean mood = false;
            if (c) {
                if (this._consumablePage < habitat.getCompatibleFields().size()) {
                    f = habitat.getCompatibleFields().get(this._consumablePage);
                    mood = digimon.getField() == f;
                } else {
                    e = habitat.getCompatibleElements().get(this._consumablePage - habitat.getCompatibleFields().size());
                    mood = digimon.getElement() == e;
                }
            } else if (this._consumablePage < habitat.getIncompatibleFields().size()) {
                f = habitat.getIncompatibleFields().get(this._consumablePage);
                mood = digimon.getField() == f;
            } else {
                e = habitat.getIncompatibleElements().get(this._consumablePage - habitat.getIncompatibleFields().size());
                mood = digimon.getElement() == e;
            }
            this._moodLabel.setVisible(mood);
            SpriteObj o = null;
            if (f != null) {
                this.checkField(f);
                o = this._fieldLabel;
                ViewUtil.centerObj(this._mainDisplay, o);
            } else if (e != null) {
                this.changeElementIcon(e);
                o = this._elementLabel;
                ViewUtil.centerObj(this._mainDisplay, o);
            }
            if (o != null) {
                boolean size;
                int pad = 0;
                if (this._moodLabel.isVisible()) {
                    pad = this._moodLabel.getLocX() / this.getScale() + this._moodLabel.getWidth() / this.getScale();
                    o.setLocX(pad / 2 + this._leftButton.getWidth() / this.getScale() / 2);
                }
                o.moveDown(7);
                boolean bl2 = size = (c ? habitat.getCompatibleElements().size() + habitat.getCompatibleFields().size() : habitat.getIncompatibleElements().size() + habitat.getIncompatibleFields().size()) > 1;
                if (size) {
                    this._rightButton.setAltIcon("tSmall");
                    ViewUtil.centerObj(o, this._rightButton);
                    this._rightButton.setLocX(o.getWidth() / this.getScale() + o.getLocX() / this.getScale() + 3);
                    this._leftButton.setAltIcon("tSmall");
                    ViewUtil.centerObj(o, this._leftButton);
                    this._leftButton.setLocX(o.getLocX() / this.getScale() - 9);
                    obj.add(this._rightButton);
                    obj.add(this._leftButton);
                }
                this._leftButton.setVisible(size);
                this._rightButton.setVisible(size);
            }
        }
        int width = 80 * this.getScale();
        int nameWidth = 65 * this.getScale();
        int margin = 0;
        int fontSize = 18 * this.getScale();
        String style = "<p style=\"text-align:center;font-size:" + fontSize + "px;font-weight:bold;width:" + nameWidth + "px;margin-bottom:" + margin + "px;\">";
        this._consumableDescription.setText("<html><div style=\"width:" + width + "px\">" + style + (c ? "Compatible" : "Incompatible") + "</p>" + style + (isEmpty ? "NA" : "") + "</p><p></p></div></html>");
        this._consumableDescription.setVisible(true);
        if (this._enterButton.isVisible()) {
            obj.add(this._enterButton);
        }
        obj.add(this._backButton);
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
        this.checkMenuAnims(m, digimon);
    }

    private void drawHabitatDescription(boolean isShop) {
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Habitat habitat = digimon.getHabitats().get(this._habitat);
        this._backButton.setVisible(true);
        this._enterButton.setAltIcon("enterButton");
        this._enterButton.setSizeX(18);
        this._enterButton.setLoc(107 - this._xPad, 56 - this._yPad);
        this._enterButton.setVisible(true);
        int width = 80 * this.getScale();
        int nameWidth = 44 * this.getScale();
        int margin = 1 * this.getScale();
        this._consumableDescription.setText("<html><div style=\"width:" + width + "px\"><p style=\"text-align:center;font-weight:bold;width:" + nameWidth + "px;margin-bottom:" + margin + "px;\">" + habitat.getName() + "</p><p>" + habitat.getDescription() + "</p><p>" + (isShop ? "&nbsp;Price: " + habitat.getPrice() : "") + "</p></div></html>");
        this._consumableDescription.setVisible(true);
        Component[] array = new SpriteObj[]{this._enterButton, this._backButton};
        this._keyboard.addInteractiveButtons(array);
    }

    private void drawHabitatInventory(Enum.Menu lastMenu) {
        this.drawHabitats(false, lastMenu);
    }

    private void drawHabitats(boolean isShop, Enum.Menu lastMenu) {
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Habitat habitat = null;
        if (isShop) {
            if (this._habitat >= 0 && this._habitat < digimon.getHabitats().size() && !digimon.getHabitats().get(this._habitat).getUnlocked() && digimon.getHabitats().get(this._habitat).getPrice() > 0) {
                habitat = digimon.getHabitats().get(this._habitat);
            } else {
                this._habitat = 0;
                for (Habitat h : digimon.getHabitats()) {
                    if (isShop ? !h.getUnlocked() && h.getPrice() > 0 : h.getUnlocked()) {
                        habitat = h;
                        break;
                    }
                    ++this._habitat;
                }
            }
        } else if (lastMenu != Enum.Menu.Habitat_Description) {
            habitat = digimon.getCurrentHabitat();
            this._habitat = habitat.getID();
        } else {
            habitat = digimon.getHabitats().get(this._habitat);
        }
        if (habitat != null) {
            this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle(), this._habitat);
        } else if (isShop) {
            this._consumableDescription.setText("<html><p style=\"text-align:center;width:" + 80 * this.getScale() + "px;font-size:" + 24 * this.getScale() + "px;font-weight:bold;\">Sold<br>Out</p></html>");
            this._consumableDescription.setVisible(true);
            this._habitat = -1;
            this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        }
        if (habitat != null) {
            this._enterButton.setAltIcon("enterButton");
            this._enterButton.setSizeX(18);
            this._enterButton.setLoc(107 - this._xPad, 56 - this._yPad);
            this._enterButton.setVisible(true);
        }
        this._backButton.setVisible(true);
        if (digimon.getIsHome() || isShop) {
            this._leftButton.setLoc(28 - this._xPad, 73 - this._yPad);
            this._rightButton.setLoc(116 - this._xPad, 73 - this._yPad);
            this._leftButton.setAltIcon("highlightLeft");
            this._rightButton.setAltIcon("highlightRight");
            this._leftButton.setVisible(true);
            this._rightButton.setVisible(true);
        }
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._enterButton, this._rightButton});
    }

    private void drawCardShop() {
        this._backgroundAnim.checkBackNoAnim(this._controller.getModel().getDigimon(), this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        this._battleButton.setIsEnabled(true);
        this._roomEffect.setAltIcon("shopClosed");
        this._roomEffect.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
    }

    private void drawMultiValidation() {
        this._battleButton.setIsEnabled(true);
        this._userInputTitle.setVisible(false);
        this._backButton.setVisible(true);
        this._backButton.setVisible(true);
        this._hostOption.setVisible(true);
        this._connectOption.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._hostOption, this._connectOption, this._backButton});
    }

    private void drawHostNameMenu(String title, String text) {
        this.resetBack();
        this._menuInteract.setVisible(false);
        this._userInputTitle.setText(title);
        this._userInputTitle.setVisible(true);
        this._closeButton.setLocX(167);
        this._closeButton.setLocY(1);
        this._closeButton.setVisible(true);
        this._enterButton.setLocX(149);
        this._enterButton.setLocY(39);
        this._enterButton.setVisible(true);
        this._stringPane.setText(text);
        this._stringPane.selectAll();
        this._stringPane.setVisible(true);
        this._stringPane.requestFocus();
        int x = this._hostNameMenu.getSizeX();
        int y = this._hostNameMenu.getSizeY();
        this._display.setSize(x, y);
        this._mainDisplay.setSize(x, y);
        this._interact.setSize(x, y);
        this._menuInteract.setSize(x, y);
        this._mainInteract.setSize(x, y);
        this._mainInteract.setLocation(0, 0);
        this._back.setSize(x, y);
        this._back.setLocation(0, 0);
        this.setSize(x, y);
        this._hostNameMenu.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new Component[]{this._stringPane, this._enterButton, this._closeButton});
    }

    private void drawVSMenu() {
        this._battleButton.setIsEnabled(true);
        this._tourneyOption.setText("Tourney");
        this._tourneyOption.setLocX(46 - this._xPad);
        this._tourneyOption.setLocY(62 - this._yPad);
        this._tourneyOption.setSize(80, 24);
        this._tourneyOption.setVisible(true);
        this._multiOption.setText("Multi");
        this._multiOption.setLocX(61 - this._xPad);
        this._multiOption.setLocY(86 - this._yPad);
        this._multiOption.setSize(50, 18);
        this._multiOption.setVisible(true);
        this._backButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._tourneyOption, this._multiOption, this._backButton});
    }

    private void drawJogressMismatch() {
        this.disposeMusic();
        this._menuButton.setVisible(true);
        this._roomEffect.setVisible(true);
        this._roomEffect.setAltIcon("mismatch");
        this._roomEffect.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
    }

    private void drawConnectError() {
        this._menuButton.setVisible(true);
        this._roomEffect.setAltIcon("connectionError");
        this._roomEffect.setVisible(true);
        this._keyboard.setCursorPosition(0);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
    }

    private void setupClock(boolean timeSkip) {
        this._hoursPane.setFont(this._bit.deriveFont((float)(36 * this.getScale())));
        this._minutesPane.setFont(this._bit.deriveFont((float)(36 * this.getScale())));
        this._colonLabel.setFont(this._bit.deriveFont((float)(48 * this.getScale())));
        int x = 18;
        if (timeSkip && Config._disablePauseOnTimeSkip && !Config._canChangeClockSpeed) {
            x = 25;
        }
        this._hoursPane.setLocation(x * this.getScale(), (62 - this._yPad) * this.getScale());
        this._minutesPane.setLocation(this._hoursPane.getX() + 36 * this.getScale(), this._hoursPane.getY());
        this._pauseButton.setLoc(this._minutesPane.getX() / this.getScale() + this._minutesPane.getWidth() / this.getScale() - 8, this._minutesPane.getY() / this.getScale() + 15);
        this._colonLabel.setLocX(this._minutesPane.getX() / this.getScale() - 10);
        this._colonLabel.setLocY(73 - this._yPad);
        this._colonLabel.setVisible(true);
        this._plusHoursButton.setLocX(this._hoursPane.getX() / this.getScale());
        this._plusHoursButton.setLocY(this._hoursPane.getY() / this.getScale() - 7);
        this._plusHoursButton.setVisible(true);
        this._minusHoursButton.setLocX(this._hoursPane.getX() / this.getScale());
        this._minusHoursButton.setLocY(this._hoursPane.getY() / this.getScale() + 31);
        this._minusHoursButton.setVisible(true);
        this._plusMinutesButton.setLocX(this._minutesPane.getX() / this.getScale());
        this._plusMinutesButton.setLocY(this._minutesPane.getY() / this.getScale() - 7);
        this._plusMinutesButton.setVisible(true);
        this._minusMinutesButton.setLocX(this._minutesPane.getX() / this.getScale());
        this._minusMinutesButton.setLocY(this._minutesPane.getY() / this.getScale() + 31);
        this._minusMinutesButton.setVisible(true);
        this._fastClockButton.setLoc(this._minusMinutesButton.getX() / this.getScale() + this._minusMinutesButton.getWidth() / this.getScale() + 1, this._minusHoursButton.getY() / this.getScale() + 3);
        this._fastClockDisplay.setLoc(this._fastClockButton.getX() / this.getScale(), this._fastClockButton.getY() / this.getScale());
        this._hoursPane.setVisible(true);
        this._minutesPane.setVisible(true);
        this.setTime();
        this._backButton.setVisible(true);
        this._backButton.setVisible(true);
    }

    private void checkTourneyAlarmSwitch(PhysicalState digimon) {
        this._optionButton.setVisible(true);
        if (this.getCurrentSelectedTrophy(digimon).getID() == digimon.getTourneyAlarm()) {
            this._optionButton.setAltIcon("alarm");
        } else {
            this._optionButton.setAltIcon("tAlarm");
        }
    }

    private void checkAutoCare(boolean a) {
        if (a) {
            this._optionButton.setAltIcon("alarmSwitch");
        } else {
            this._optionButton.setAltIcon("tAlarmSwitch");
        }
    }

    private void setCurrentAlarmTime() {
        if (this._controller.getModel().getTime().getAlarmMinutes() >= 0) {
            byte[] time = this._controller.getModel().getTime().getTimeFromMinutes(this._controller.getModel().getTime().getAlarmMinutes());
            this._hoursPane.setText(this.getExtraZero(Byte.toString(time[0])));
            this._minutesPane.setText(this.getExtraZero(Byte.toString(time[1])));
        }
    }

    private void drawAutoCareValidation() {
        this._statusButton.setIsEnabled(true);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._backButton.setVisible(true);
        this.checkAutoCare(digimon.getAutoCare());
        this._optionButton.setSize(14, 14);
        this._optionButton.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._optionButton.getWidth() / this.getScale() - 4, this._mainDisplay.getHeight() / this.getScale() / 2 - this._optionButton.getHeight() / this.getScale() / 2 + 6);
        this._optionButton.setVisible(true);
        this._bitsLabel.setRawLoc(0 * this.getScale(), this._optionButton.getY() - 3 * this.getScale());
        this._bitsLabel.setVisible(true);
        int dWidth = 80 * this.getScale();
        int nameWidth = 54 * this.getScale();
        int marginName = 0 * this.getScale();
        int marginDescription = 3 * this.getScale();
        int margin = 0 * this.getScale();
        int hourPrice = 0;
        int carePrice = 0;
        switch (digimon.getGrowthStage()) {
            case Egg: {
                hourPrice = Config._autoCareStageIHourPrice;
                carePrice = Config._autoCareStageIPrice;
                break;
            }
            case Fresh: {
                hourPrice = Config._autoCareStageIHourPrice;
                carePrice = Config._autoCareStageIPrice;
                break;
            }
            case InTraining: {
                hourPrice = Config._autoCareStageIIHourPrice;
                carePrice = Config._autoCareStageIIPrice;
                break;
            }
            case Rookie: {
                hourPrice = Config._autoCareStageIIIHourPrice;
                carePrice = Config._autoCareStageIIIPrice;
                break;
            }
            case Champion: {
                hourPrice = Config._autoCareStageIVHourPrice;
                carePrice = Config._autoCareStageIVPrice;
                break;
            }
            case Ultimate: {
                hourPrice = Config._autoCareStageVHourPrice;
                carePrice = Config._autoCareStageVPrice;
                break;
            }
            case Mega: {
                hourPrice = Config._autoCareStageVIHourPrice;
                carePrice = Config._autoCareStageVIPrice;
            }
        }
        String hour = hourPrice > 0 ? "&nbsp;" + hourPrice + "/hour<br>" : "";
        String care = "&nbsp;" + carePrice + "/care";
        this.drawConsumableDescription("AI Assistant", hour + care, dWidth, nameWidth, marginName, marginDescription, margin, 15 * this.getScale(), 15 * this.getScale(), 50 * this.getScale());
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._optionButton, this._backButton});
    }

    private void drawSetAlarmMenu(boolean timeSkip) {
        this.setupClock(timeSkip);
        this.setCurrentAlarmTime();
        this._optionButton.setSize(14, 14);
        this._optionButton.setLoc(-1 + this._pauseButton.getLocX() / this.getScale(), this._pauseButton.getLocY() / this.getScale());
        this._optionButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._plusHoursButton, this._minusHoursButton, this._plusMinutesButton, this._minusMinutesButton, this._optionButton, this._backButton});
    }

    private void changeFastClockDisplayWidth(int speed) {
        switch (speed) {
            case 2: {
                this._fastClockDisplay.setSizeX(14);
                break;
            }
            case 3: {
                this._fastClockDisplay.setSizeX(21);
                break;
            }
            case 4: {
                this._fastClockDisplay.setSizeX(28);
                break;
            }
            default: {
                this._fastClockDisplay.setSizeX(7);
            }
        }
    }

    private void drawSetClockMenu(boolean timeSkip) {
        this.setupClock(timeSkip);
        ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>(Arrays.asList(this._plusHoursButton, this._minusHoursButton, this._plusMinutesButton, this._minusMinutesButton, this._backButton));
        if (this.canChangeFastClock()) {
            this._fastClockDisplay.setAltIcon("tFastClock");
            this.changeFastClockDisplayWidth(this._controller.getModel().getTime().getFastMod());
            this._fastClockButton.setVisible(true);
            this._fastClockDisplay.setVisible(true);
            obj.add(4, this._fastClockButton);
        }
        if (!timeSkip || !Config._disablePauseOnTimeSkip) {
            this._pauseButton.setVisible(true);
            obj.add(4, this._pauseButton);
        }
        this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
    }

    private void drawAttackMenu() {
        this._attackOption.setLocX(39 - this._xPad);
        this._attackOption.setLocY(68 - this._yPad);
        this._attackOption.drawNumMirror(0, false);
        this._attackOption.setVisible(true);
        this._surrenderOption.setText("");
        this._surrenderOption.setSize(30, 33);
        this._surrenderOption.setLocX(this._attackOption.getLocX() / this.getScale() + 48);
        this._surrenderOption.setLocY(this._attackOption.getLocY() / this.getScale());
        this._surrenderOption.drawNumMirror(2, false);
        this._surrenderOption.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._attackOption, this._surrenderOption});
    }

    private void drawAttackTypeMenu() {
        this._attackOption.setVisible(false);
        this.drawAttackTypes();
        this.checkHealth(this._controller.getBattle().getHealth(), this._controller.getBattle().getFullHealth());
        this._healthBar.setLocX(-this._healthBar.getSizeX() / this.getScale() + this._mainDisplay.getWidth() / this.getScale());
        this._healthBarFull.setLocX(-this._healthBar.getSizeX() / this.getScale() + this._mainDisplay.getWidth() / this.getScale());
        this._healthBarFull.setVisible(true);
        this._healthBar.setVisible(true);
        String num = this._controller.getBattle().getHealth() + " / " + this._controller.getBattle().getFullHealth();
        this._consumableDescription.setText("<html><div style=\"width:" + 105 * this.getScale() + "px;text-align:right;\"><div style=\"padding-bottom:" + 36 * this.getScale() + "px;text-align:center;display:inline-block;font-size:" + 14 * this.getScale() + "px;\">HP " + num + "</div></div></html>");
        this._consumableDescription.setVisible(true);
        this._cardButton.setLoc(this._vaccineAttack.getLocX() / this.getScale() - 1, this._vaccineAttack.getLocY() / this.getScale() + 15);
        this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum()]);
        this._cardButton.setVisible(true);
        try {
            this._participants[0].setLoc(3, -19 + this._mainDisplay.getHeight() / this.getScale());
            this._participants[0].setSize(16, 16);
            this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[0], (double)(this.getScale() / this.getScale()) / 3.0));
        }
        catch (NullPointerException e) {
            this._participants[0].setLoc(0, -27 + this._mainDisplay.getHeight() / this.getScale());
            this._participants[0].setSize((int)((double)(this._battleBags.getSizeX() / this.getScale()) / 3.0), (int)((double)(this._battleBags.getSizeY() / this.getScale()) / 3.0));
            this._participants[0].setIcon(ViewUtil.resizeImage(this._battleBags.getSpriteSheet()[0], (double)(this.getScale() / this.getScale()) / 3.0));
        }
        this._participants[0].setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._vaccineAttack, this._virusAttack, this._dataAttack, this._cardButton, this._participants[0], this._backButton});
    }

    private void drawAttackTypes() {
        this._vaccineAttack.setLocX(71 - this._xPad);
        this._vaccineAttack.setLocY(12 + this._backButton.getLocY() / this.getScale());
        this._vaccineAttack.setVisible(true);
        this._virusAttack.setLocX(92 - this._xPad);
        this._virusAttack.setLocY(100 - this._yPad);
        this._virusAttack.setVisible(true);
        this._dataAttack.setLocX(49 - this._xPad);
        this._dataAttack.setLocY(100 - this._yPad);
        this._dataAttack.setVisible(true);
        this._backButton.setVisible(true);
        this._backButton.setVisible(true);
    }

    private void drawEnemyAttacks() {
        String level = "" + this._controller.getBattle().getEnemyLevel();
        this._consumableDescription.setText("<html><div style=\"width:" + 110 * this.getScale() + "px;text-align:right;\"><div style=\"padding-bottom:" + 0 * this.getScale() + "px;text-align:center;display:inline-block;font-size:" + 14 * this.getScale() + "px;\">LV " + level + "</div></div></html>");
        this._consumableDescription.setVisible(true);
        String num = this._controller.getBattle().getEnemyHealth() + " / " + this._controller.getBattle().getEnemy().getEnemyHealth();
        this._messageDisplay.setText("<html><div style=\"width:" + 105 * this.getScale() + "px;text-align:right;\"><div style=\"padding-bottom:" + 36 * this.getScale() + "px;text-align:center;display:inline-block;font-size:" + 14 * this.getScale() + "px;\">HP " + num + "</div></div></html>");
        this._messageDisplay.setVisible(true);
        this.drawAttackTypes();
        this.checkHealth(this._controller.getBattle().getEnemyHealth(), this._controller.getBattle().getEnemy().getEnemyHealth());
        this._healthBar.setLocX(-this._healthBar.getSizeX() / this.getScale() + this._mainDisplay.getWidth() / this.getScale());
        this._healthBarFull.setLocX(-this._healthBar.getSizeX() / this.getScale() + this._mainDisplay.getWidth() / this.getScale());
        this._healthBarFull.setVisible(true);
        this._healthBar.setVisible(true);
        this._participants[0].setLoc(70 - this._xPad, this._vaccineAttack.getLocY() / this.getScale() + 21);
        this._participants[0].setSize(16, 16);
        this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[6], (double)(this.getScale() / this.getScale()) / 3.0));
        this._participants[0].setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._vaccineAttack, this._virusAttack, this._dataAttack, this._backButton});
    }

    private void drawAttackDescription() {
        this.drawDescription(this._controller.getModel().getDigimon().getIndex());
    }

    private void drawEnemyAttackDescription() {
        if (this._controller.getBattle() != null) {
            this.drawDescription(this._controller.getBattle().getEnemy().getIndex());
        } else {
            this.drawDescription(-1);
        }
    }

    private void drawDescription(int index) {
        EvolutionInfo d = new EvolutionInfo();
        if (index != -1) {
            d = this._controller.getModel().getDigimon().getEvolution().getDigimon(index);
        }
        this._backButton.setVisible(true);
        int x = 113 - this._xPad;
        int y = 57 - this._yPad;
        String attack = "";
        Enum.AttackEffect effect = null;
        ArrayList<Enum.AttackCondition> conditions = null;
        switch (this._animValue) {
            case 0: {
                this._vaccineAttack.setLocX(x);
                this._vaccineAttack.setLocY(y);
                this._vaccineAttack.setVisible(true);
                attack = d.getVaccineName();
                effect = d.getVaccineEffect();
                conditions = d.getVaccineConditions();
                break;
            }
            case 1: {
                this._dataAttack.setLocX(x);
                this._dataAttack.setLocY(y);
                this._dataAttack.setVisible(true);
                attack = d.getDataName();
                effect = d.getDataEffect();
                conditions = d.getDataConditions();
                break;
            }
            case 2: {
                this._virusAttack.setLocX(x);
                this._virusAttack.setLocY(y);
                this._virusAttack.setVisible(true);
                attack = d.getVirusName();
                effect = d.getVirusEffect();
                conditions = d.getVirusConditions();
            }
        }
        AttackEffectProcess p = new AttackEffectProcess(null);
        this._consumableDescription.setText(p.getAttackDescription(this.getScale(), attack, effect, conditions));
        this._consumableDescription.setVisible(true);
        this.addAttackInteractiveButtons();
    }

    private void addAttackInteractiveButtons() {
        if (this._controller.getCurrentMenu() == Enum.Menu.Attack_Description && this._controller.getBattle() != null && this._controller.getBattle().getBattleType() != Battle.BattleType.None) {
            switch (this._animValue) {
                case 0: {
                    this._keyboard.addInteractiveButtons(new SpriteObj[]{this._vaccineAttack, this._backButton});
                    break;
                }
                case 1: {
                    this._keyboard.addInteractiveButtons(new SpriteObj[]{this._dataAttack, this._backButton});
                    break;
                }
                case 2: {
                    this._keyboard.addInteractiveButtons(new SpriteObj[]{this._virusAttack, this._backButton});
                }
            }
        } else {
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
        }
    }

    private void drawInvestigateMenu() {
        this.drawSurrenderMenu();
        this._surrenderOption.setSize(110, 21);
        this._surrenderOption.setLoc(6, 60 - this._yPad);
        this._surrenderOption.setText("Investigate");
    }

    private void drawClockValidation() {
        this._surrenderOption.setVisible(false);
        this._surrenderOption.setSize(120, 18);
        this._surrenderOption.removeIcon();
        this._surrenderOption.setLoc(12, 61 - this._yPad);
        this._surrenderOption.setText("Set " + this.getExtraZero(Integer.toString(this._controller.getModel().getTime().getHours())) + ":" + this.getExtraZero(Integer.toString(this._controller.getModel().getTime().getMinutes())) + "?");
        this._surrenderOption.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(40 - this._xPad);
        this._yesLabel.setLocY(82 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(82 - this._yPad);
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void drawSurrenderMenu() {
        this._surrenderOption.setVisible(false);
        this._surrenderOption.setSize(100, 18);
        this._surrenderOption.removeIcon();
        if (this._controller.getBattle() != null && this._controller.getBattle().getBattleType().equals((Object)Battle.BattleType.PvE_Wild)) {
            this._surrenderOption.setText("Escape");
            this._surrenderOption.setLoc(24, 60 - this._yPad);
        } else {
            this._surrenderOption.setText("Surrender");
            this._surrenderOption.setLoc(10, 60 - this._yPad);
        }
        this._surrenderOption.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(84 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(84 - this._yPad);
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void drawMapSelect(boolean home) {
        this._backButton.setVisible(true);
        this._battleButton.setIsEnabled(true);
        this.setMapPage(this._consumablePage, home);
        this._map.setLoc(44 - this._xPad, 59 - this._yPad);
        this._map.setVisible(true);
        this._leftButton.setAltIcon("highlightLeft");
        this._rightButton.setAltIcon("highlightRight");
        this._leftButton.setLoc(29 - this._xPad, 71 - this._yPad);
        this._leftButton.setVisible(true);
        this._rightButton.setLoc(119 - this._xPad, 71 - this._yPad);
        this._rightButton.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._map, this._rightButton, this._backButton});
    }

    private void drawZoneSelect(boolean show) {
        this._backButton.setVisible(true);
        if (show) {
            this._battleButton.setIsEnabled(true);
        }
        this._chooseMaps.setAltIcon("tChangeMaps");
        this._map.setVisible(false);
        this._travelLabel.setVisible(false);
        this._chooseMaps.setVisible(false);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (!digimon.getIsHome()) {
            WorldMap world = digimon.getWorld();
            MapLevel currentMap = world.getCurrentMap();
            if (currentMap != null) {
                for (int i = 0; i < currentMap.getZones().size(); ++i) {
                    Zone zone = currentMap.getZones().get(i);
                    if (zone == null) continue;
                    if (!this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                        if (zone.getIsComplete()) {
                            this._zoneButtons.get(i).setAltIcon("zoneComplete");
                        } else if (zone.getIsCurrent() && this._zoneButtons.get(i).getIcon() == null) {
                            this._zoneButtons.get(i).setAltIcon("zoneComplete");
                        } else {
                            this._zoneButtons.get(i).removeIcon();
                        }
                    }
                    this._zoneButtons.get(i).setVisible(true);
                }
            }
            this.checkMap(digimon.getWorld().getCurrentMap());
            this._map.setLoc(this.MAP_LOC.x, this.MAP_LOC.y);
            this._map.setVisible(true);
            ArrayList<SpriteObj> obj = new ArrayList<SpriteObj>();
            if (show) {
                this.checkTravelLabel(world, true);
                this._travelLabel.setLoc(26 - this._xPad, 90 - this._yPad);
                this._travelLabel.setVisible(true);
                this._chooseMaps.setVisible(true);
                obj.add(this._chooseMaps);
                obj.add(this._travelLabel);
            }
            if (currentMap != null && currentMap.getZones() != null) {
                for (int i = 0; i < this._zoneButtons.size(); ++i) {
                    obj.add(this._zoneButtons.get(i));
                }
            }
            if (show) {
                obj.add(this._backButton);
            }
            this._keyboard.addInteractiveButtons(obj.toArray(new SpriteObj[obj.size()]));
        } else {
            this._menuButton.setVisible(true);
            this._roomEffect.setAltIcon("world");
            this._roomEffect.setVisible(true);
            this._keyboard.setCursorPosition(0);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
        }
    }

    private void drawSteps() {
        this._backButton.setVisible(true);
        this._battleButton.setIsEnabled(true);
        this._stepsLabel.setLoc(56 - this._xPad, 58 - this._yPad);
        this._stepsLabel.setVisible(true);
        do {
            try {
                this._stepsPanel.setText("<html><p  style=\"margin-top:10\">" + this._selectZone.getCurrentLocation() + "&nbsp;/</p><p  style=\"margin-top:-6\">&nbsp;&nbsp;&nbsp;" + this._selectZone.getTotalSteps() + "</p></html>");
                this._stepsPanel.setLoc(43 - this._xPad, 64 - this._yPad + (this.getScale() != 1 ? 4 : 0));
            }
            catch (NullPointerException e) {
                e.printStackTrace();
            }
        } while (this._stepsPanel.getText().equals(""));
        this._stepsPanel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._backButton});
    }

    private void drawZoneValidation() {
        this._consumableDescription.setText("<html><div style=margin-top:" + 6 * this.getScale() + "px;\"height:" + 0 * this.getScale() + "px;text-align:center;font-size:" + 20 * this.getScale() + "px;\">Use 1 Zone<br>Transport</div><div style=\"width:" + 78 * this.getScale() + "px;text-align:center;\"><div style=\"text-align:center;display:inline-block;font-size:" + 29 * this.getScale() + "px;\">&nbsp;</div></div></html>");
        this._consumableDescription.setVisible(true);
        this._okValidation.setText("");
        this._okValidation.setSize(34, 18);
        this._okValidation.setLoc(63 - this._xPad, 59 - this._yPad);
        this._okValidation.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(92 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(this._yesLabel.getLocY() / this.getScale());
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void drawZoneDetail() {
        try {
            this._backButton.setVisible(true);
            this._battleButton.setIsEnabled(true);
            this._enterButton.setAltIcon("enterButton");
            this._enterButton.setSizeX(18);
            this._enterButton.setLoc(107 - this._xPad, 56 - this._yPad);
            this._enterButton.setVisible(true);
            this._zoneDetail.setLoc(2, this._mainDisplay.getHeight() / this.getScale() - this._zoneDetail.getSizeY() / this.getScale());
            this._zoneDetail.setVisible(true);
            this.checkAdventureDetails();
            this._adventureBar.setVisible(true);
            this._leftButton.setLoc(45 - this._xPad, 93 - this._yPad);
            this._rightButton.setLoc(103 - this._xPad, 93 - this._yPad);
            this._leftButton.setVisible(true);
            this._rightButton.setVisible(true);
            this._rightButton.setAltIcon("tSmall");
            this._leftButton.setAltIcon("tSmall");
            this._participants[0].setSize(16, 16);
            this._participants[0].setLoc(this._adventureBar.getX() / this.getScale() - this._participants[0].getSizeX() / (this.getScale() * 2), this._adventureBar.getY() / this.getScale() - this._participants[0].getSizeY() / this.getScale() - 2);
            this._participants[0].setIcon(ViewUtil.resizeImage(this._character.getSpriteSheet()[0], 0.3333333333333333));
            this._participants[0].setVisible(true);
            this.drawTowns(this._controller.getModel().getDigimon().getWorld().getCurrentZone());
            this._townLabel.setVisible(true);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._leftButton, this._rightButton, this._enterButton, this._backButton});
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void drawMapValidation() {
        this._consumableDescription.setText("<html><div style=\"height:" + 0 * this.getScale() + "px;text-align:center;font-size:" + 20 * this.getScale() + "px;\">Use 1 Continent<br>Transport</div><div style=\"width:" + 80 * this.getScale() + "px;text-align:center;\"><div style=\"text-align:center;display:inline-block;font-size:" + 29 * this.getScale() + "px;\">&nbsp;</div></div></html>");
        this._consumableDescription.setVisible(true);
        this._okValidation.setText("");
        this._okValidation.setSize(34, 18);
        this._okValidation.setLoc(63 - this._xPad, 59 - this._yPad);
        this._okValidation.setVisible(true);
        this._yesLabel.setText("Yes");
        this._yesLabel.setLocX(38 - this._xPad);
        this._yesLabel.setLocY(92 - this._yPad);
        this._yesLabel.setSizeX(36);
        this._noLabel.setLocX(this._yesLabel.getLocX() / this.getScale() + this._yesLabel.getSizeX() / this.getScale() + 18);
        this._noLabel.setLocY(this._yesLabel.getLocY() / this.getScale());
        this._noLabel.setVisible(true);
        this._yesLabel.setVisible(true);
        this._keyboard.addInteractiveButtons(new SpriteObj[]{this._yesLabel, this._noLabel});
    }

    private void setTicBarSize() {
        byte seconds = this._controller.getModel().getTime().getSeconds();
        if (seconds >= 0 && seconds < 10) {
            this._ticBar.setSizeX(0);
        } else if (seconds >= 10 && seconds < 20) {
            this._ticBar.setSizeX(8);
        } else if (seconds >= 20 && seconds < 30) {
            this._ticBar.setSizeX(16);
        } else if (seconds >= 30 && seconds < 40) {
            this._ticBar.setSizeX(24);
        } else if (seconds >= 40 && seconds < 50) {
            this._ticBar.setSizeX(32);
        } else if (seconds >= 50 && seconds < 60) {
            this._ticBar.setSizeX(40);
        }
    }

    public void checkEggLabel(ArrayList<EvolutionInfo> digimon) {
        EvolutionInfo e = digimon.get(this._consumablePage);
        SpriteObj o = this.getOppSet(e.getNewStage(), e.getNewSpriteSet(), e.getNewSpriteNum());
        this._eggLabel.setIcon(o.getSpriteSheet()[0]);
    }

    public void checkAnims(Enum.Menu currentMenu, PhysicalState digimon) {
        ArrayList animQueue = digimon.getAnimQueue();
        if (this._character == null || this._isLoaded) {
            this.getCharSprite();
            this.setSpriteCharDefault();
            this._isLoaded = false;
        }
        if (currentMenu == Enum.Menu.None) {
            this.checkCurrentAnim();
            if (!Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentAnim)) {
                if (this._currentAnim != Enum.State.Pooping && this._currentAnim != Enum.State.Cleaning && this._currentAnim != Enum.State.Retreating || this._currentAnim == Enum.State.Evolving) {
                    this._filthLabel.setVisible(false);
                }
                switch (this._currentAnim) {
                    case EvolSilhouetteBack: {
                        this.evolSilhouetteBack(digimon);
                        break;
                    }
                    case EvolSilhouetteTransition: {
                        this.evolSilhouetteTransition();
                        break;
                    }
                    case Buying_Food: {
                        this.transactionAnim(this._currentAnim);
                        break;
                    }
                    case Buying_Habitat: {
                        this.transactionAnim(this._currentAnim);
                        break;
                    }
                    case Buying_Item: {
                        this.transactionAnim(this._currentAnim);
                        break;
                    }
                    case Selling_Food: {
                        this.transactionAnim(this._currentAnim);
                        break;
                    }
                    case Selling_Item: {
                        this.transactionAnim(this._currentAnim);
                        break;
                    }
                    case EarningBits_Tourney: {
                        this.transactionAnim(Enum.State.EarningBits_Tourney);
                        break;
                    }
                    case Tourney_Start: {
                        this.tourneyStart();
                        break;
                    }
                    case PerfectWinsInc: {
                        this.perfectWinsInc();
                        break;
                    }
                    case HealthInc: {
                        this.healthInc();
                        break;
                    }
                    case ZoneChange: {
                        this.zoneChange();
                        break;
                    }
                    case Tourney_Trophy: {
                        this.tourneyTrophy();
                        break;
                    }
                    case NPC_Fight: {
                        this.npcFight();
                        break;
                    }
                    case Jogress_Flash: {
                        this.jogressFlash();
                        break;
                    }
                    case Jogress_Start: {
                        this.startJogressAnim();
                        break;
                    }
                    case WaitingTurn: {
                        this.waitingTurn();
                        break;
                    }
                    case DNA_Generate: {
                        this.drawDNAGenerateAnim();
                        break;
                    }
                    case Vaccine_Training: {
                        this.preTraining(Enum.Attribute.Vaccine);
                        break;
                    }
                    case Data_Training: {
                        this.preTraining(Enum.Attribute.Data);
                        break;
                    }
                    case Virus_Training: {
                        this.preTraining(Enum.Attribute.Virus);
                        break;
                    }
                    case HP_Training: {
                        this.drawHPTraining();
                        break;
                    }
                    case HP_Training_AttackSuccess: {
                        this.drawHPTrainingAttackSuccess();
                        break;
                    }
                    case HP_Training_AttackFail: {
                        this.drawHPTrainingAttackFail();
                        break;
                    }
                    case Attacking: {
                        this.attackAnim();
                        break;
                    }
                    case Battle_Flash: {
                        this.battleFlash();
                        break;
                    }
                    case Battle_Start: {
                        this.startBattle();
                        break;
                    }
                    case Battling_PlayerAttack: {
                        this.battlePlayerShootAnim(true);
                        break;
                    }
                    case Battling_PlayerReceiveAttack: {
                        this.battlePlayerReceiveAttackAnim(true);
                        break;
                    }
                    case Battling_OpponentAttack: {
                        this.battlePlayerShootAnim(false);
                        break;
                    }
                    case Battling_OpponentReceiveAttack: {
                        this.battlePlayerReceiveAttackAnim(false);
                        break;
                    }
                    case Battling_PlayerHit: {
                        this.battlePlayerHit(true);
                        break;
                    }
                    case Battling_OpponentHit: {
                        this.battlePlayerHit(false);
                        break;
                    }
                    case Battling_PlayerHit_Aftermath: {
                        this.battlePlayerHitAftermath(true);
                        break;
                    }
                    case Battling_OpponentHit_Aftermath: {
                        this.battlePlayerHitAftermath(false);
                        break;
                    }
                    case EnemyHealing: {
                        this.heal(true);
                        break;
                    }
                    case PlayerHealing: {
                        this.heal(false);
                        break;
                    }
                    case Attack_Contact: {
                        this.hitAnim();
                        break;
                    }
                    case Attack_Aftermath: {
                        this.attackAftermath();
                        break;
                    }
                    case BossDeath: {
                        this.zoneBossDeath();
                        break;
                    }
                    case BossParade: {
                        this.bossParade();
                        break;
                    }
                    case MapComplete: {
                        this.mapComplete();
                        break;
                    }
                    case Bad_Praise: {
                        this.cheer(false, SoundConfig._happy, true);
                        break;
                    }
                    case Bad_Scold: {
                        boolean angry = digimon.getDisposition() < 0;
                        this.jeer(angry, angry ? SoundConfig._angry : SoundConfig._unhappy, true);
                        break;
                    }
                    case NormalMorning: {
                        this.wakeUp(7, true);
                        break;
                    }
                    case GoodMorning: {
                        this.wakeUp(5, true);
                        break;
                    }
                    case BadMorning: {
                        this.wakeUp(9, true);
                        break;
                    }
                    case TerribleMorning: {
                        this.wakeUp(6, true);
                        break;
                    }
                    case Cheering: {
                        this.cheer(true, SoundConfig._happy, true);
                        break;
                    }
                    case Jeering: {
                        this.jeer(true, SoundConfig._angry, true);
                        break;
                    }
                    case Sad_Jeering: {
                        this.jeer(false, SoundConfig._unhappy, true);
                        break;
                    }
                    case Bad_Health_Jeering: {
                        this.badHealthJeer();
                        break;
                    }
                    case Retreating: {
                        this.retreat(digimon.getDisposition() != -1);
                        break;
                    }
                    case Losing: {
                        this.losing();
                        break;
                    }
                    case Winning: {
                        this.winning();
                        break;
                    }
                    case Hatching: {
                        this.hatch();
                        break;
                    }
                    case Cleaning: {
                        this.clean();
                        break;
                    }
                    case Refusing: {
                        this.refuse();
                        break;
                    }
                    case Pooping: {
                        this.poop();
                        break;
                    }
                    case Pooping_Outside_Move: {
                        this.poopOutsideMove();
                        break;
                    }
                    case Pooping_Outside: {
                        this.poopOutside();
                        break;
                    }
                    case Pooping_Outside_Return: {
                        this.poopOutsideReturn();
                        break;
                    }
                    case Eating: {
                        this.eat(Enum.State.Eating);
                        break;
                    }
                    case Munching: {
                        this.eat(Enum.State.Munching);
                        break;
                    }
                    case DisposeFood: {
                        this.disposeFood();
                        break;
                    }
                    case Assistant_Feed: {
                        this.assistantFeed();
                        break;
                    }
                    case Assistant_Clean: {
                        this.assistantClean();
                        break;
                    }
                    case Assistant_Lights: {
                        this.assistantLights(digimon);
                        break;
                    }
                    case Birthday_Bad: {
                        this.birthdayDrop(digimon.getUnlockConsumable());
                        break;
                    }
                    case Birthday_Normal: {
                        this.birthdayDrop(digimon.getUnlockConsumable());
                        break;
                    }
                    case Birthday_Good: {
                        this.birthdayDrop(digimon.getUnlockConsumable());
                        break;
                    }
                    case X_Program: {
                        this.xProgram();
                        break;
                    }
                    case X_AntibodyInc: {
                        this.xAntibodyInc();
                        break;
                    }
                    case DNA_Feeding: {
                        this.dnaCharge();
                        break;
                    }
                    case Bandaging: {
                        this.bandage();
                        break;
                    }
                    case Teleport_Leave: {
                        this.teleportLeave();
                        break;
                    }
                    case Teleport_Arrive: {
                        this.teleportArrive();
                        break;
                    }
                    case Evolving: {
                        this.digivolve();
                        break;
                    }
                    case Jogress: {
                        this.jogress();
                        break;
                    }
                    case ItemEvol: {
                        this.itemEvolve();
                        break;
                    }
                    case Retreat_Town: {
                        this.retreatToTown();
                        break;
                    }
                    case LifeInc: {
                        this.changeLife(digimon.getWorld().getAdventureLife() - 1);
                        break;
                    }
                    case LifeDec: {
                        this.changeLife(digimon.getWorld().getAdventureLife() + 1);
                        break;
                    }
                    case Recover: {
                        this.recover();
                        break;
                    }
                    case Play: {
                        this.playing(Enum.State.Cheering);
                        break;
                    }
                    case PlayAngry: {
                        this.playing(Enum.State.Jeering);
                        break;
                    }
                    case AngrySurprise: {
                        this.angrySurprise(Enum.State.Jeering);
                        break;
                    }
                    case Bounce: {
                        this.bouncing();
                        break;
                    }
                    case Ride: {
                        this.riding();
                        break;
                    }
                    case Study: {
                        this.studying();
                        break;
                    }
                    case PortToilet: {
                        this.portToilet();
                        break;
                    }
                    case Toilet: {
                        this.toilet();
                        break;
                    }
                    case SelfToilet: {
                        this.selfToilet();
                        break;
                    }
                    case SelfPortToilet: {
                        this.selfPortToilet();
                        break;
                    }
                    case Interact: {
                        this.interactingSound(Enum.State.Cheering);
                        break;
                    }
                    case InteractAngry: {
                        this.interactingSound(Enum.State.Jeering);
                        break;
                    }
                    case InteractXylophone: {
                        this.interactXylophone();
                        break;
                    }
                    case InteractToyOven: {
                        this.interactToyOven();
                        break;
                    }
                    case InteractTelevision: {
                        this.interactTelevision();
                        break;
                    }
                    case InteractComputer: {
                        this.interactComputer();
                        break;
                    }
                    case Jump: {
                        this.jumping();
                        break;
                    }
                    case Lift: {
                        this.lifting();
                        break;
                    }
                    case Bathe: {
                        this.bathing();
                        break;
                    }
                    case Shower: {
                        this.showering();
                        break;
                    }
                    case UnlockItem: {
                        this.unlocking(true, digimon.getUnlockConsumable());
                        break;
                    }
                    case UnlockFood: {
                        this.unlocking(false, digimon.getUnlockConsumable());
                        break;
                    }
                    case UnlockDNA: {
                        this.unlockingDNA(Enum.Field.values()[digimon.getUnlockConsumable()]);
                        break;
                    }
                    case EarningBits: {
                        this.transactionAnim(Enum.State.EarningBits);
                        break;
                    }
                    case UnlockInheritance: {
                        this.unlocking(true, 32);
                        break;
                    }
                    case Inherit: {
                        this.inheriting();
                        break;
                    }
                    case BirdraTransport: {
                        this.transportAnim(Enum.State.BirdraTransport, 0);
                        break;
                    }
                    case GarudaTransport: {
                        this.transportAnim(Enum.State.GarudaTransport, 0);
                        break;
                    }
                    case PhoenixTransport: {
                        this.transportAnim(Enum.State.PhoenixTransport, this._selectZone.getZoneNum() - 1);
                        break;
                    }
                    case WhaTransport: {
                        this.transportAnim(Enum.State.WhaTransport, -1);
                        break;
                    }
                    case WhaTransportFade: {
                        this.whaTransportFade();
                        break;
                    }
                    case WhaTransportSwim: {
                        this.whaTransportSwim();
                        break;
                    }
                    case WhaTransportArrive: {
                        this.whaTransportArrive();
                        break;
                    }
                    case Pausing: {
                        this.pause(digimon);
                        break;
                    }
                    case Unpausing: {
                        this.unpause(digimon);
                        break;
                    }
                    case GiftCall: {
                        this.attention(5, 7);
                        break;
                    }
                    case Gifting: {
                        this.gifting();
                        break;
                    }
                    case Discovering: {
                        this.investigateLeft(Enum.State.Discovering);
                        break;
                    }
                    case DiscoverEnemy: {
                        this.investigateLeft(Enum.State.DiscoverEnemy);
                        break;
                    }
                    case ReturnItem: {
                        this.returnItem();
                        break;
                    }
                    case DiscoverCall: {
                        this.attention(5, 7);
                        break;
                    }
                    case Requesting: {
                        break;
                    }
                    case RequestCall: {
                        this.attention(5, 7);
                        break;
                    }
                    case TournamentAlert: {
                        this.attention(6, 1);
                        break;
                    }
                    case Dying: {
                        this.dying();
                        break;
                    }
                    case Dead: {
                        this.deading();
                    }
                }
            } else {
                boolean currentAnimContainsIdle = Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentAnim);
                boolean currentStateContainsIdle = Utility.containsState(Utility.ENABLE_DURING_STATE, digimon.getCurrentState());
                this.idle(currentAnimContainsIdle, currentStateContainsIdle);
                if (!animQueue.isEmpty() && currentAnimContainsIdle && this._currentAnim != null) {
                    this.checkAnimQueue(animQueue);
                }
                if (animQueue.isEmpty() && currentAnimContainsIdle && currentStateContainsIdle) {
                    digimon.setCanEvolveOrDie(true);
                }
            }
            ++this._frame;
            ++this._stateFrame;
        } else {
            this.checkMenuAnims(currentMenu, digimon);
        }
    }

    private void checkMenuAnims(Enum.Menu currentMenu, PhysicalState digimon) {
        switch (currentMenu) {
            case Data_Status: {
                if (!Config._showWeightArrow) break;
                this.drawWeightAnim(digimon);
                break;
            }
            case Buy_Nutrition: 
            case Use_Nutrition: 
            case Med_Nutrition: 
            case Sell_Nutrition: 
            case Data_Nutrition: {
                this.drawNutritionAnim(currentMenu, digimon);
                break;
            }
            case SetDifficulty: {
                this.drawDifficultyMenuAnim();
                break;
            }
            case EvolSilhouette: {
                this.drawSilhouetteAnim();
                break;
            }
            case EvolutionState: {
                if (!digimon.getAlive()) break;
                this.drawEvolutionStateAnim();
                break;
            }
            case ZoneDetail: {
                this.drawZoneDetailAnim();
                break;
            }
            case Roster: {
                this.drawRosterAnim();
                break;
            }
            case Attack_Validation: {
                if (this._animValue == 5) {
                    this.cycleAnim(this._attackOption, 0);
                    break;
                }
                if (this._animValue != 7) break;
                this.cycleAnim(this._surrenderOption, 2);
                break;
            }
            case AttackType_Validation: {
                if (this._animValue == 5) {
                    this.rotateCard();
                }
                this.drawAttackTypeValidationAnim();
                break;
            }
            case Enemy_Attacks: {
                this.drawEnemyAttacksAnim();
                break;
            }
            case Set_EggClock: {
                this.clockAnim();
                break;
            }
            case Data_Clock: {
                this.checkClock();
                this.clockAnim();
                break;
            }
            case Data_HP: {
                this.drawHPAnim();
                break;
            }
            case Habitat_Compatibility: 
            case Habitat_Shop_Compatibility: {
                Habitat habitat;
                if (!this._moodLabel.isVisible() || !(habitat = digimon.getHabitats().get(this._habitat)).getCompatibleElements().contains((Object)digimon.getElement()) && !habitat.getCompatibleFields().contains((Object)digimon.getField())) break;
                this.moodAnim(Enum.Mood.Happy);
                break;
            }
            case Habitat_Incompatibility: 
            case Habitat_Shop_Incompatibility: {
                Habitat habitat;
                if (!this._moodLabel.isVisible() || !(habitat = this._controller.getModel().getDigimon().getHabitats().get(this._habitat)).getIncompatibleElements().contains((Object)digimon.getElement()) && !habitat.getIncompatibleFields().contains((Object)digimon.getField())) break;
                this.moodAnim(Enum.Mood.Unhappy);
                break;
            }
            case Data_Energy: {
                this.moodAnim(digimon.getCurrentMood());
                break;
            }
            case Data_Temp: {
                if (!this._tempDrag) {
                    this.setupTempBar(digimon.getTemp());
                    this.setupCurrentTemp(digimon.getTemp());
                }
                this.drawTempAnim();
                this.moodAnim(digimon.checkIdealTemp());
                break;
            }
            case Set_Clock: {
                this.clockAnim();
                break;
            }
            case ChooseZone: 
            case MapZoneSelect: {
                this.zoneAnim();
                break;
            }
            case Royale_Lineup: {
                if (this._frame <= 0 || this._frame >= 5 * this._interval) {
                    this._frame = 0;
                }
                this.royaleAnim();
            }
        }
        ++this._frame;
    }

    private void drawWeightAnim(PhysicalState digimon) {
        int rate = 3 * this._interval;
        if (this._frame == 0) {
            if (digimon.getCalories() > 0) {
                this.drawWeightArrow(true, 0);
            } else if (digimon.getCalories() < 0) {
                this.drawWeightArrow(false, 0);
            }
        } else if (this._frame == rate) {
            if (digimon.getCalories() > 0) {
                this.drawWeightArrow(true, -2);
            } else if (digimon.getCalories() < 0) {
                this.drawWeightArrow(false, -6);
            }
        } else if (this._frame == rate * 2) {
            if (digimon.getCalories() > 0) {
                this.drawWeightArrow(true, -4);
            } else if (digimon.getCalories() < 0) {
                this.drawWeightArrow(false, -4);
            }
        } else if (this._frame == rate * 3) {
            if (digimon.getCalories() > 0) {
                this.drawWeightArrow(true, -6);
            } else if (digimon.getCalories() < 0) {
                this.drawWeightArrow(false, -2);
            }
            this._frame = -rate;
        } else if (this._frame > rate * 3) {
            this._frame = -1;
        }
    }

    private void drawWeightArrow(boolean positive, int y) {
        int rotations = positive ? 1 : 3;
        Icon r = ViewUtil.cropImage(this._select.getIcon(), this._select.getWidth() - 2 * this.getScale(), this._select.getHeight());
        Icon i = ViewUtil.getRotatedIcon(rotations, r);
        BufferedImage arrow = ViewUtil.createBuffImage(i);
        BufferedImage screen = new BufferedImage(this._roomEffect.getSizeX(), this._roomEffect.getSizeY(), 2);
        Graphics2D g2 = screen.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        g2.drawImage(arrow, null, this._weightLabel.getLocX() + 1 * this.getScale(), this._weightLabel.getLocY() - arrow.getHeight() + y * this.getScale());
        g2.dispose();
        this._roomEffect.setIcon(new ImageIcon(screen));
        this._roomEffect.setVisible(true);
    }

    private void drawRosterAnim() {
        Icon icon;
        int i;
        Tournament t = this._controller.getModel().getDigimon().getTournament();
        if (this._frame < -8 * this._interval || this._frame > 8 * this._interval) {
            for (i = 0; i < this._participants.length; ++i) {
                if (t.getDisqualified().contains(t.getRoster()[i])) {
                    icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 10, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                } else if (t.getRoster()[i] != null) {
                    icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 0, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                } else {
                    this._participants[i].setIcon(ViewUtil.resizeImage(this._participants[i].getSpriteSheet()[this._participants[i].getSpriteNum()], (double)(this.getScale() / this.getScale()) / 3.0));
                }
                this._participants[i].setVisible(true);
            }
            this._frame = 0;
        }
        if (this._frame == 0 * this._interval) {
            for (i = 0; i < this._participants.length; ++i) {
                if (t.getDisqualified().contains(t.getRoster()[i])) {
                    icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 10, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                } else if (t.getRoster()[i] != null) {
                    icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 0, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                } else {
                    this._participants[i].setIcon(ViewUtil.resizeImage(this._participants[i].getSpriteSheet()[this._participants[i].getSpriteNum()], (double)(this.getScale() / this.getScale()) / 3.0));
                }
                this._participants[i].setVisible(true);
            }
        } else if (this._frame == 7 * this._interval) {
            for (i = 0; i < this._participants.length; ++i) {
                if (t.getDisqualified().contains(t.getRoster()[i])) {
                    icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 9, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                } else if (t.getRoster()[i] != null) {
                    icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 1, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                } else {
                    this._participants[i].setIcon(ViewUtil.resizeImage(this._participants[i].getSpriteSheet()[this._participants[i].getSpriteNum() + 1], (double)(this.getScale() / this.getScale()) / 3.0));
                }
                this._participants[i].setVisible(true);
            }
            this._frame = -7 * this._interval;
        }
    }

    private void drawAttackTypeValidationAnim() {
        if (this._participants[0] != null) {
            if (this._frame < -10 * this._interval || this._frame > 10 * this._interval) {
                this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[0], (double)(this.getScale() / this.getScale()) / 3.0));
                this._participants[0].setVisible(true);
                this._frame = 0;
            }
            if (this._frame == 0 * this._interval) {
                this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[0], (double)(this.getScale() / this.getScale()) / 3.0));
                this._participants[0].setVisible(true);
            } else if (this._frame == 8 * this._interval) {
                this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[1], (double)(this.getScale() / this.getScale()) / 3.0));
                this._participants[0].setVisible(true);
                this._frame = -8 * this._interval;
            }
        }
    }

    private void rotateCard() {
        if (this._frame < -10 * this._interval || this._frame > 10 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum()]);
            this._frame = 0;
        }
        if (this._frame == 0 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum()]);
        } else if (this._frame == 2 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum() + 1]);
        } else if (this._frame == 4 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum() + 2]);
        } else if (this._frame == 6 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum() + 3]);
        } else if (this._frame == 8 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum()]);
        } else if (this._frame == -6 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum() + 1]);
        } else if (this._frame == -4 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum() + 2]);
        } else if (this._frame == -2 * this._interval) {
            this._cardButton.setIcon(this._cardButton.getSpriteSheet()[this._cardButton.getSpriteNum() + 3]);
        }
        this._cardButton.setVisible(true);
    }

    private void cycleAnim(SpriteObj obj, int spriteNum) {
        if (this._frame < -2 * this._interval || this._frame > 2 * this._interval) {
            obj.setIcon(obj.getSpriteSheet()[spriteNum + 1]);
            this._frame = 0;
        }
        if (this._frame == 0 * this._interval) {
            obj.setIcon(obj.getSpriteSheet()[spriteNum]);
        } else if (this._frame == 2 * this._interval) {
            obj.setIcon(obj.getSpriteSheet()[spriteNum + 1]);
            this._frame = -2 * this._interval;
        }
        obj.setVisible(true);
    }

    private void drawTempAnim() {
        if (!(this._tempDrag || this._frame != 0 && this._frame % (7 * this._interval) != 0)) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            if (digimon.getTempGoal() <= 100 && digimon.getTempGoal() != digimon.getTemp() && !digimon.pauseTemp()) {
                if (digimon.getTempGoal() > digimon.getTemp()) {
                    if (this._tempArrow.getLocX() / this.getScale() >= this._mainDisplay.getWidth() / this.getScale() - 39 + this._tempArrow.getSizeX() / this.getScale() * 2) {
                        this._tempArrow.setLocX(this._mainDisplay.getWidth() / this.getScale() - 39);
                    } else {
                        this._tempArrow.setLocX(this._tempArrow.getLocX() / this.getScale() + this._tempArrow.getSizeX() / this.getScale());
                    }
                } else if (digimon.getTempGoal() < digimon.getTemp()) {
                    if (this._tempArrow.getLocX() / this.getScale() <= 34 - this._tempArrow.getSizeX() / this.getScale() * 2) {
                        this._tempArrow.setLocX(34);
                    } else {
                        this._tempArrow.setLocX(this._tempArrow.getLocX() / this.getScale() - this._tempArrow.getSizeX() / this.getScale());
                    }
                }
                this._tempArrow.setVisible(true);
            } else {
                this._tempArrow.setVisible(false);
            }
        }
    }

    private void drawDifficultyMenuAnim() {
        if (this._frame == 0) {
            if (this._border.getX() <= this._opponent.getLocX()) {
                this._opponent.drawNumMirror(4, false);
            } else if (this._border.getX() <= this._character.getLocX()) {
                this._character.drawNumMirror(4, false);
            } else {
                this._eggLabel.drawNumMirror(4, false);
            }
        } else if (this._frame >= 9) {
            this._frame = -9;
            if (this._border.getX() <= this._opponent.getLocX()) {
                this._opponent.drawNumMirror(6, false);
            } else if (this._border.getX() <= this._character.getLocX()) {
                this._character.drawNumMirror(6, false);
            } else {
                this._eggLabel.drawNumMirror(6, false);
            }
        }
        if (!(this._border.isVisible() || this._opponent.getSpriteNum() == 0 && this._character.getSpriteNum() == 0 && this._eggLabel.getSpriteNum() == 0)) {
            this._opponent.drawNumMirror(0, false);
            this._character.drawNumMirror(0, false);
            this._eggLabel.drawNumMirror(0, false);
        }
    }

    private void drawSilhouetteAnim() {
        int factor = Integer.parseInt(this._digicore.getName()) * 4 * this._interval;
        if (factor <= 0) {
            factor = 1;
        }
        if (this._frame == 0) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            ArrayList<EvolutionInfo> evolutions = digimon.getEvolution().getCurrentNaturalEvol(digimon);
            if (evolutions != null && this._frame / factor < evolutions.size()) {
                this.drawSilhouette(evolutions, this._frame / factor);
            } else if (evolutions == null) {
                this.setEvolvingIcon(this._frame / factor);
            }
        } else if (this._frame % factor == 0) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            ArrayList<EvolutionInfo> evolutions = digimon.getEvolution().getCurrentNaturalEvol(digimon);
            if (evolutions != null && this._frame / factor < evolutions.size()) {
                this.drawSilhouette(evolutions, this._frame / factor);
                if (this._frame / factor == evolutions.size() - 1) {
                    this._frame = -factor;
                }
            } else if (evolutions == null && this._frame / factor < 4) {
                this.setEvolvingIcon(this._frame / factor);
                if (this._frame / factor == 3) {
                    this._frame = -factor;
                }
            } else {
                this._frame = -factor;
            }
        }
        if (this._frame == 0 || this._frame % factor == 0) {
            if (this._frame / factor % 2 == 0) {
                this._opponent.moveDown(1);
                this._background.moveRight(5);
            } else {
                this._opponent.moveUp(1);
                this._background.moveLeft(5);
            }
        }
    }

    private void setEvolvingIcon(int sprite) {
        Icon i = ViewUtil.getIndividualIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "evolving.png", (double)this.getScale() * 3.0, 0, sprite >= 0 ? sprite : 0, 14, 15, 1);
        this._opponent.setIcon(i);
        this._opponent.setVisible(true);
    }

    private void drawDNAGenerateAnim() {
        double rate = 0.0;
        if (this._frame <= 0 * this._interval) {
            this._controller.slowClock();
            this.drawDNAGenerate();
            this._frame = 0;
        } else if (this._frame > 0) {
            double time = (double)this._frame / ((double)this._interval * 10.0);
            rate = Math.ceil((double)this._controller.getNumHits() / time * 10.0);
            String s = (int)rate > 9 ? (int)rate + "" : "0" + (int)rate;
            this._rate.setText(s);
            double percent = rate / 80.0;
            this._rateLabel.setSizeX((int)(100.0 * percent));
            this._rateLabel.setVisible(true);
            if (this._frame > 100 * this._interval) {
                this.endAnim();
                this._controller.onDNAGenerate((int)rate);
            }
        }
        int loc = 8 * this.getScale();
        if (this._frame > 10 && this._frame <= 30 * this._interval) {
            if (this._frame % (8 * this._interval) == 0) {
                this.shakeObj(this._fieldLabel, loc);
            }
        } else if (this._frame > 30 && this._frame <= 50 * this._interval) {
            if (this._frame % (4 * this._interval) == 0) {
                this.shakeObj(this._fieldLabel, loc);
            }
        } else if (this._frame > 50 && this._frame <= 80 * this._interval) {
            if (this._frame % (2 * this._interval) == 0) {
                this.shakeObj(this._fieldLabel, loc);
            }
        } else if (this._frame > 80 && this._frame <= 100 * this._interval && this._frame % (1 * this._interval) == 0) {
            this.shakeObj(this._fieldLabel, loc);
        }
        if (this._frame > 10 * this._interval && this._frame < 15 * this._interval) {
            this.checkField(this._controller.getDNARate((int)rate));
        } else if (this._frame > 20 * this._interval && this._frame < 25 * this._interval) {
            this.checkField(this._controller.getDNARate((int)rate));
        } else if (this._frame > 35 * this._interval && this._frame < 40 * this._interval) {
            this.checkField(this._controller.getDNARate((int)rate));
        } else if (this._frame > 45 * this._interval && this._frame < 55 * this._interval) {
            this.checkField(this._controller.getDNARate((int)rate));
        } else if (this._frame > 60 * this._interval && this._frame < 70 * this._interval) {
            this.checkField(this._controller.getDNARate((int)rate));
        } else if (this._frame > 80 * this._interval && this._frame <= 100 * this._interval) {
            this.checkField(this._controller.getDNARate((int)rate));
        }
    }

    private void shakeObj(SpriteObj obj, int loc) {
        if (obj.getLocX() == loc || obj.getLocX() == loc + this.getScale()) {
            obj.setRawLoc(obj.getLocX() - this.getScale(), obj.getLocY());
        } else if (obj.getLocX() == loc - this.getScale()) {
            obj.setRawLoc(obj.getLocX() + this.getScale(), obj.getLocY());
        }
    }

    private void drawEvolutionStateAnim() {
        if (this._frame == Integer.parseInt(this._digicore.getName()) * this._interval) {
            this._digicore.moveUp(1);
            this._opponent.moveDown(1);
        } else if (this._frame >= Integer.parseInt(this._digicore.getName()) * 2 * this._interval) {
            this._opponent.moveUp(1);
            this._digicore.moveDown(1);
            this._frame = 0;
        }
        this._digicore.setVisible(true);
    }

    private void drawZoneDetailAnim() {
        try {
            Icon icon;
            if (this._frame < -4 * this._interval || this._frame > 4 * this._interval) {
                icon = ViewUtil.resizeImage(this._character.getSpriteSheet()[0], 0.3333333333333333);
                if (this._controller.getModel().getDigimon().getWorld().getTravelRight()) {
                    icon = ViewUtil.flipIcon(icon);
                }
                this._participants[0].setIcon(icon);
                this._frame = 0;
            }
            if (this._frame == 0 * this._interval) {
                icon = ViewUtil.resizeImage(this._character.getSpriteSheet()[0], 0.3333333333333333);
                WorldMap world = this._controller.getModel().getDigimon().getWorld();
                if (world.getTravelRight()) {
                    icon = ViewUtil.flipIcon(icon);
                }
                this._participants[0].setIcon(icon);
                if (world.getCurrentZone().isTown() != null) {
                    this._townLabel.setVisible(!this._townLabel.isVisible());
                    this._participants[0].setVisible(!this._participants[0].isVisible());
                } else {
                    this._townLabel.setVisible(true);
                    this._participants[0].setVisible(true);
                }
            } else if (this._frame == 4 * this._interval) {
                icon = ViewUtil.resizeImage(this._character.getSpriteSheet()[1], 0.3333333333333333);
                WorldMap world = this._controller.getModel().getDigimon().getWorld();
                if (world.getTravelRight()) {
                    icon = ViewUtil.flipIcon(icon);
                }
                this._participants[0].setIcon(icon);
                if (world.getCurrentZone().isTown() != null) {
                    this._townLabel.setVisible(!this._townLabel.isVisible());
                    this._participants[0].setVisible(!this._participants[0].isVisible());
                } else {
                    this._townLabel.setVisible(true);
                    this._participants[0].setVisible(true);
                }
                this._frame = -4 * this._interval;
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    private void drawEnemyAttacksAnim() {
        if (this._frame < -8 * this._interval || this._frame > 8 * this._interval) {
            try {
                this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[6], (double)(this.getScale() / this.getScale()) / 3.0));
            }
            catch (NullPointerException e) {
                this._participants[0].setIcon(ViewUtil.resizeImage(this._battleBags.getSpriteSheet()[0], (double)(this.getScale() / this.getScale()) / 3.0));
            }
            this._participants[0].setVisible(true);
            this._frame = 0;
        }
        if (this._frame == 0 * this._interval) {
            this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[6], (double)(this.getScale() / this.getScale()) / 3.0));
            this._participants[0].setVisible(true);
        } else if (this._frame == 6 * this._interval) {
            this._participants[0].setIcon(ViewUtil.resizeImage(this._opponent.getSpriteSheet()[1], (double)(this.getScale() / this.getScale()) / 3.0));
            this._participants[0].setVisible(true);
            this._frame = -6 * this._interval;
        }
    }

    private void royaleAnim() {
        Tournament t = this._controller.getModel().getDigimon().getTournament();
        if (this._frame % (14 * this._interval) == 0) {
            if (this._frame == Integer.MAX_VALUE) {
                this._frame = 0;
            }
            for (int i = 0; i < t.getRoster().length; ++i) {
                this._participants[i].setAltIcon("zoneComplete");
                Point p = this.getParticipantRoyaleLocation(i, t);
                this._participants[i].setLoc(p.x + 3, p.y);
                this._participants[i].setSize(6, 6);
                if (t.getRoster()[i] != null) {
                    if (!t.getDisqualified().contains(t.getRoster()[i])) {
                        if (this._participants[i].isVisible()) {
                            this._participants[i].setVisible(false);
                            continue;
                        }
                        this._participants[i].setVisible(true);
                        continue;
                    }
                    this._participants[i].setVisible(true);
                    continue;
                }
                if (t.getIsWon() != 0) {
                    if (this._participants[i].isVisible()) {
                        this._participants[i].setVisible(false);
                        continue;
                    }
                    this._participants[i].setVisible(true);
                    continue;
                }
                this._participants[i].setVisible(true);
            }
        }
    }

    private Point getParticipantRoyaleLocation(int i, Tournament t) {
        int x = 0;
        int y = 0;
        block0 : switch (t.checkRound()) {
            case 1: {
                switch (i) {
                    case 0: {
                        x = 4;
                        y = 26;
                        break;
                    }
                    case 1: {
                        x = 16;
                        y = 26;
                        break;
                    }
                    case 2: {
                        x = 28;
                        y = 26;
                        break;
                    }
                    case 3: {
                        x = 40;
                        y = 26;
                        break;
                    }
                    case 4: {
                        x = 52;
                        y = 26;
                        break;
                    }
                    case 5: {
                        x = 64;
                        y = 26;
                        break;
                    }
                    case 6: {
                        x = 76;
                        y = 26;
                        break;
                    }
                    case 7: {
                        x = 88;
                        y = 26;
                    }
                }
                break;
            }
            case 2: {
                switch (i) {
                    case 0: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 4;
                            y = 26;
                            break;
                        }
                        x = 10;
                        y = 18;
                        break;
                    }
                    case 1: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 16;
                            y = 26;
                            break;
                        }
                        x = 10;
                        y = 18;
                        break;
                    }
                    case 2: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 28;
                            y = 26;
                            break;
                        }
                        x = 34;
                        y = 18;
                        break;
                    }
                    case 3: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 40;
                            y = 26;
                            break;
                        }
                        x = 34;
                        y = 18;
                        break;
                    }
                    case 4: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 52;
                            y = 26;
                            break;
                        }
                        x = 58;
                        y = 18;
                        break;
                    }
                    case 5: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 64;
                            y = 26;
                            break;
                        }
                        x = 58;
                        y = 18;
                        break;
                    }
                    case 6: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 76;
                            y = 26;
                            break;
                        }
                        x = 82;
                        y = 18;
                        break;
                    }
                    case 7: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || t.getPlayerIndex() == i && t.getIsWon() == 0) {
                            x = 88;
                            y = 26;
                            break;
                        }
                        x = 82;
                        y = 18;
                    }
                }
                break;
            }
            case 3: {
                int playerIndex = t.getPlayerIndex();
                switch (i) {
                    case 0: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[1]) || playerIndex == 1 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[3]) || playerIndex == 3 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[2]) || playerIndex == 2 && t.getIsWon() == 0)) {
                                x = 4;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 22;
                                y = 10;
                                break block0;
                            }
                            x = 4;
                            y = 26;
                            break block0;
                        }
                        x = 22;
                        y = 10;
                        break block0;
                    }
                    case 1: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[0]) || playerIndex == 0 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[2]) || playerIndex == 2 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[3]) || playerIndex == 3 && t.getIsWon() == 0)) {
                                x = 16;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 22;
                                y = 10;
                                break block0;
                            }
                            x = 16;
                            y = 26;
                            break block0;
                        }
                        x = 22;
                        y = 10;
                        break block0;
                    }
                    case 2: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[3]) || playerIndex == 3 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[1]) || playerIndex == 1 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[0]) || playerIndex == 0 && t.getIsWon() == 0)) {
                                x = 28;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 22;
                                y = 10;
                                break block0;
                            }
                            x = 28;
                            y = 26;
                            break block0;
                        }
                        x = 22;
                        y = 10;
                        break block0;
                    }
                    case 3: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[2]) || playerIndex == 2 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[1]) || playerIndex == 1 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[0]) || playerIndex == 0 && t.getIsWon() == 0)) {
                                x = 40;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 22;
                                y = 10;
                                break block0;
                            }
                            x = 40;
                            y = 26;
                            break block0;
                        }
                        x = 22;
                        y = 10;
                        break block0;
                    }
                    case 4: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[5]) || playerIndex == 5 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[7]) || playerIndex == 7 && t.getIsWon() == 0) && t.getDisqualified().contains(t.getRoster()[6]) || playerIndex == 6 && t.getIsWon() == 0) {
                                x = 52;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 70;
                                y = 10;
                                break block0;
                            }
                            x = 52;
                            y = 26;
                            break block0;
                        }
                        x = 70;
                        y = 10;
                        break block0;
                    }
                    case 5: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[4]) || playerIndex == 4 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[7]) || playerIndex == 7 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[6]) || playerIndex == 6 && t.getIsWon() == 0)) {
                                x = 64;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 70;
                                y = 10;
                                break block0;
                            }
                            x = 64;
                            y = 26;
                            break block0;
                        }
                        x = 70;
                        y = 10;
                        break block0;
                    }
                    case 6: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[7]) || playerIndex == 7 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[5]) || playerIndex == 5 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[4]) || playerIndex == 4 && t.getIsWon() == 0)) {
                                x = 76;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 70;
                                y = 10;
                                break block0;
                            }
                            x = 76;
                            y = 26;
                            break block0;
                        }
                        x = 70;
                        y = 10;
                        break block0;
                    }
                    case 7: {
                        if (t.getDisqualified().contains(t.getRoster()[i]) || playerIndex == i && t.getIsWon() == 0) {
                            if ((t.getDisqualified().contains(t.getRoster()[6]) || playerIndex == 6 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[5]) || playerIndex == 5 && t.getIsWon() == 0) && (t.getDisqualified().contains(t.getRoster()[4]) || playerIndex == 4 && t.getIsWon() == 0)) {
                                x = 88;
                                y = 26;
                                break block0;
                            }
                            if (t.getIsWon() == 2) {
                                x = 70;
                                y = 10;
                                break block0;
                            }
                            x = 88;
                            y = 26;
                            break block0;
                        }
                        x = 70;
                        y = 10;
                    }
                }
            }
        }
        return new Point(x, y);
    }

    private void clockAnim() {
        if (this._frame >= this._interval * 0) {
            if (this._colonLabel.getText().equals(":")) {
                this._colonLabel.setText("");
            } else {
                this._colonLabel.setText(":");
            }
            this._frame = -7 * this._interval;
        }
    }

    private void zoneAnim() {
        if (!this._controller.getModel().getDigimon().getIsHome() && this._frame >= this._interval * 0) {
            MapLevel currentMap = this._controller.getModel().getDigimon().getWorld().getCurrentMap();
            if (currentMap != null) {
                for (int i = 0; i < currentMap.getZones().size(); ++i) {
                    Zone zone = currentMap.getZones().get(i);
                    if (zone == null) continue;
                    if (!this._controller.getModel().getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) {
                        if (zone.getIsCurrent() && this._zoneButtons.get(i).getIcon() == null) {
                            this._zoneButtons.get(i).setAltIcon("zoneComplete");
                            break;
                        }
                        if (zone.getIsCurrent()) {
                            this._zoneButtons.get(i).removeIcon();
                            break;
                        }
                    }
                    this._zoneButtons.get(i).setVisible(true);
                }
            }
            this._frame = -7 * this._interval;
        }
    }

    private void drawTempMoodArrow(PhysicalState digimon, int frame) {
        if (digimon.tempTooHigh()) {
            if (frame == 1) {
                this._tempMoodArrow.setIcon(ViewUtil.flipVertically(this._tempMoodArrow.getAltSprite("tempArrow")));
            } else {
                this._tempMoodArrow.setIcon(ViewUtil.flipVertically(this._tempMoodArrow.getAltSprite("tempArrow2")));
            }
        } else if (frame == 1) {
            this._tempMoodArrow.setAltIcon("tempArrow");
        } else {
            this._tempMoodArrow.setAltIcon("tempArrow2");
        }
        this._tempMoodArrow.setVisible(true);
    }

    private void recoveryAnim(boolean r) {
        if (this._frame % (this._interval * 7) == 0) {
            if (r) {
                this._recoveryLabel.drawNumMirror(this._recoveryLabel.getSpriteNum() == 2 ? 3 : 2, false);
            } else {
                this._recoveryLabel.drawNumMirror(this._recoveryLabel.getSpriteNum() == 0 ? 1 : 0, false);
            }
        }
        this._recoveryLabel.setVisible(true);
    }

    private void drawHPAnim() {
        if (this._frame % (this._interval * 7) == 0) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            this.getHPText(digimon.getHealthPoints(), digimon.getFullHealthPoints());
            this.checkHealth(digimon.getHealthPoints(), digimon.getFullHealthPoints());
            this.recoveryAnim(digimon.isFullyRecovered());
        } else if (this._frame >= 7 * this._interval) {
            this._frame = -7 * this._interval;
        }
    }

    private void drawFoodGroupIcon(PhysicalState digimon) {
        int size = this._foodType.getType().size() + 1;
        int factor = 10 * this._interval;
        if (factor <= 0) {
            factor = 1;
        }
        if (this._frame == 0) {
            if (this._frame / factor < this._foodType.getType().size()) {
                this.setFoodGroupIcon(this._frame / factor);
            } else if (this._foodType.getType().contains((Object)digimon.getDislikedFood())) {
                this._foodLabel.setIcon(this._moodLabel.getAltSprite("unhappy"));
            } else if (this._foodType.getType().contains((Object)digimon.getFavFood())) {
                this._foodLabel.setIcon(this._moodLabel.getAltSprite("happy"));
            } else {
                this._frame = -this._interval;
            }
        } else if (this._frame > 0 && this._frame % factor == 0) {
            if (this._frame / factor < size) {
                if (this._frame / factor < this._foodType.getType().size()) {
                    this.setFoodGroupIcon(this._frame / factor);
                } else if (this._foodType.getType().contains((Object)digimon.getDislikedFood())) {
                    this._foodLabel.setIcon(this._moodLabel.getAltSprite("unhappy"));
                } else if (this._foodType.getType().contains((Object)digimon.getFavFood())) {
                    this._foodLabel.setIcon(this._moodLabel.getAltSprite("happy"));
                } else {
                    this._frame = -this._interval;
                }
                if (this._frame / factor == size - 1) {
                    this._frame = -factor;
                }
            } else {
                this._frame = -factor;
            }
        }
    }

    private void drawNutritionAnim(Enum.Menu menu, PhysicalState digimon) {
        switch (menu) {
            case Data_Nutrition: {
                this.recoveryAnim(digimon.getGoodNutrition());
                if (this._frame * this._interval < 7 * this._interval) break;
                this._frame = -7 * this._interval;
                break;
            }
            default: {
                this.drawFoodGroupIcon(digimon);
            }
        }
    }

    private void moodAnim(Enum.Mood mood) {
        boolean isTemp;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        boolean bl = isTemp = this._controller.getCurrentMenu() == Enum.Menu.Data_Temp;
        if (this._frame <= this._interval * 0) {
            this._frame = 14 * this._interval;
            switch (mood) {
                case Happy: {
                    this._moodLabel.setAltIcon("happy");
                    this._tempMoodArrow.setVisible(false);
                    break;
                }
                case Unhappy: {
                    if (isTemp) {
                        this.drawTempMoodArrow(digimon, 1);
                    }
                    this._moodLabel.setAltIcon("unhappy");
                    break;
                }
                case Depressed: {
                    this._tempMoodArrow.setVisible(false);
                    this._moodLabel.setAltIcon("depressed");
                    break;
                }
                case Neutral: {
                    this._moodLabel.removeIcon();
                    this._moodLabel.setText(this.scaleTextPadding("."));
                    this._tempMoodArrow.setVisible(false);
                }
            }
        } else if (this._frame == this._interval * 14) {
            switch (mood) {
                case Happy: {
                    this._moodLabel.setAltIcon("happy");
                    this._tempMoodArrow.setVisible(false);
                    break;
                }
                case Unhappy: {
                    if (isTemp) {
                        this.drawTempMoodArrow(digimon, 1);
                    }
                    this._moodLabel.setAltIcon("unhappy");
                    break;
                }
                case Depressed: {
                    this._tempMoodArrow.setVisible(false);
                    this._moodLabel.setAltIcon("depressed");
                    break;
                }
                case Neutral: {
                    this._moodLabel.removeIcon();
                    this._moodLabel.setText(this.scaleTextPadding("."));
                    this._tempMoodArrow.setVisible(false);
                }
            }
        } else if (this._frame == this._interval * 21) {
            switch (mood) {
                case Happy: {
                    this._moodLabel.setAltIcon("happy2");
                    this._frame = 7 * this._interval;
                    this._tempMoodArrow.setVisible(false);
                    break;
                }
                case Unhappy: {
                    if (isTemp) {
                        this.drawTempMoodArrow(digimon, 2);
                    }
                    this._moodLabel.setAltIcon("unhappy2");
                    this._frame = 7 * this._interval;
                    break;
                }
                case Depressed: {
                    this._tempMoodArrow.setVisible(false);
                    this._moodLabel.setAltIcon("depressed2");
                    this._frame = 7 * this._interval;
                    break;
                }
                case Neutral: {
                    this._moodLabel.removeIcon();
                    this._moodLabel.setText(this.scaleTextPadding(".."));
                    this._tempMoodArrow.setVisible(false);
                }
            }
        } else if (this._frame == this._interval * 28) {
            switch (mood) {
                case Neutral: {
                    this._moodLabel.removeIcon();
                    this._moodLabel.setText(this.scaleTextPadding("..."));
                }
            }
        } else if (this._frame >= this._interval * 35) {
            switch (mood) {
                case Neutral: {
                    this._moodLabel.removeIcon();
                    this._moodLabel.setText(this.scaleTextPadding(".."));
                }
            }
            this._frame = 7 * this._interval;
        }
        this._moodLabel.setVisible(true);
    }

    private String scaleTextPadding(String content) {
        int padding = 11 * this.getScale();
        return "<html><p style=\"padding-bottom:" + padding + "\">" + content + "</p></html>";
    }

    private void disableExtraLabels() {
        this._roomEffect.removeIcon();
        this._emotionLabel.setVisible(false);
        this._foodLabel.setVisible(false);
    }

    private void checkCurrentAnim() {
        if (this._currentAnim == null || this._currentAnim == Enum.State.None) {
            this._currentAnim = this._controller.getModel().getDigimon().getCurrentState();
            if (this._currentAnim != Enum.State.Idling) {
                this.disableMainMenu();
            } else {
                this.enableMainMenu();
            }
        }
    }

    private void checkAnimQueue(ArrayList<Enum.State> animQueue) {
        this._currentAnim = null;
        this._controller.getModel().getDigimon().setCurrentState(animQueue.get(0));
        animQueue.remove(0);
        if (!animQueue.isEmpty()) {
            animQueue.trimToSize();
        }
        this._frame = this._interval * -1;
    }

    private void getCharSprite() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (!digimon.getAlive()) {
            this.setDeathIcon();
        } else if (digimon.getGrowthStage() == Enum.Stage.Egg) {
            SpriteObj character = this.getOppSet(digimon.getGrowthStage(), digimon.getSpriteSet(), digimon.getSpriteNum(), false);
            this._character.setSpriteSheet(character.getSpriteSheet());
            this._character.setSpriteSheetMirror(character.getSpriteSheetMirror());
            this._character.setSpriteLoc(character.getSpriteLoc());
            this._character.drawNumMirror(0, false);
        } else {
            SpriteObj character = this.getOppSet(digimon.getGrowthStage(), digimon.getSpriteSet(), digimon.getSpriteNum(), true);
            this._character.setSpriteSheet(character.getSpriteSheet());
            this._character.setSpriteSheetMirror(character.getSpriteSheetMirror());
            this._character.setSpriteLoc(character.getSpriteLoc());
            this._character.drawNumMirror(0, false);
        }
    }

    private void hideSpriteSetsExcept(Enum.Stage stage, int spriteSet) {
    }

    public void drawMainBackground(Enum.Menu currentMenu) {
        if (currentMenu == Enum.Menu.Start || currentMenu == Enum.Menu.Set_EggClock || currentMenu == Enum.Menu.Save_Name || currentMenu == Enum.Menu.Load_Name || currentMenu == Enum.Menu.SetDifficulty || currentMenu == Enum.Menu.Host_Name_Battle || currentMenu == Enum.Menu.Host_Name_Jogress || currentMenu == Enum.Menu.Settings || currentMenu == Enum.Menu.Host_Port_Battle || currentMenu == Enum.Menu.Host_Port_Jogress) {
            this._shell.setVisible(false);
        }
        this._rect.setVisible(currentMenu == Enum.Menu.None && this._currentAnim != Enum.State.Data_Training && this._currentAnim != Enum.State.HP_Training && !Utility.containsState(Utility.DISABLE_RAIN_DURING_STATE, this._currentAnim));
        if (this._message != null && this._weather.getOverlay().isVisible()) {
            this._weather.getOverlay().setVisible(false);
        }
    }

    public void checkWeather(Enum.Menu currentMenu, PhysicalState myDigimon, Battle battle) {
        if (this._message == null && !this._pauseWeather && this._weather != null && currentMenu == Enum.Menu.None && !Utility.containsState(Utility.DISABLE_RAIN_DURING_STATE, this._currentAnim)) {
            Enum.Weather weather = myDigimon.getCurrentWeather();
            if (weather == Enum.Weather.Clear || weather == Enum.Weather.Cloudy) {
                this._weather.getOverlay().setVisible(false);
                this._weather.stopWeather();
                if (this._currentWeather != weather) {
                    if (this._currentWeather != Enum.Weather.Clear && this._currentWeather != Enum.Weather.Cloudy) {
                        this._backgroundAnim.checkBack(myDigimon, currentMenu, this.getScale(), battle, this._habitat);
                    } else {
                        this._backgroundAnim.setupBack(myDigimon, this.getScale());
                    }
                    this._currentWeather = weather;
                }
            } else {
                this._weather.getOverlay().setVisible(true);
                this._weather.precipitate(weather, 0, this._rect);
                if (this._currentWeather != weather) {
                    if (this._currentWeather == Enum.Weather.Clear || this._currentWeather == Enum.Weather.Cloudy) {
                        this._backgroundAnim.checkBack(myDigimon, currentMenu, this.getScale(), battle, this._habitat);
                    }
                    this._weather.startWeather(weather);
                    this._currentWeather = weather;
                }
                this._weather.toggleWeatherSound(true, weather);
            }
        } else if (this._weather != null) {
            this._weather.toggleWeatherSound(false, Enum.Weather.Clear);
            this._weather.getOverlay().setVisible(false);
        }
    }

    public void repositionMain() {
        int x = this._controller.getWindowLocX();
        int y = this._controller.getWindowLocY();
        this.setLocation(x, y);
    }

    /*
     * Enabled aggressive exception aggregation
     */
    private String[] getDigicoreConfig(PhysicalState digimon) {
        String[] info = new String[3];
        try (InputStream in = this.getClass().getResourceAsStream(File.separator + "Model" + File.separator + "digicoreMenuConfig.csv");){
            String[] stringArray;
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
                String line = reader.readLine();
                while ((line = reader.readLine()) != null) {
                    String[] test = line.split(",");
                    if (Integer.parseInt(test[0]) != digimon.getIndex()) continue;
                    for (int i = 0; i < test.length; ++i) {
                        info[i] = test[i];
                    }
                }
                stringArray = info;
            }
            return stringArray;
        }
        catch (Exception e) {
            return info;
        }
    }

    public void checkMap(MapLevel map) {
        String spriteName = map.getImage();
        SpriteObj obj = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, spriteName, null, this.MAP_SIZE.x, this.MAP_SIZE.y, this.getScale());
        Icon icon = obj.getIcon();
        this._map.setIcon(icon);
    }

    public void setupShell(Shell s) {
        BufferedImage sheet = ViewUtil.createBuffImage(ViewUtil.resizeImage(ViewUtil.getResource(this.MOD_FOLDER, this.RESOURCES_FOLDER, s.getFileName()), (double)this.getScale()));
        this._mainBackground.setIcon(new ImageIcon(sheet.getSubimage(0, 0, s.getSize()[0] * this.getScale(), s.getSize()[1] * this.getScale())));
        ViewUtil.setBackgroundColor(this, s.isTransparent() ? 0.0f : 1.0f);
        this.setShellComponent(sheet, this._settingsButton, s.getConfigSheetLoc(), s.getConfigRolloverSheetLoc(), s.getConfigSize(), s.getConfigShellLoc());
        this.setShellComponent(sheet, this._evolutionTreeButton, s.getEvolSheetLoc(), s.getEvolRolloverSheetLoc(), s.getEvolSize(), s.getEvolShellLoc());
        this.setShellComponent(sheet, this._mapButton, s.getMapSheetLoc(), s.getMapRolloverSheetLoc(), s.getMapSize(), s.getMapShellLoc());
        this.setShellComponent(sheet, this._clockButton, s.getClockSheetLoc(), s.getClockRolloverSheetLoc(), s.getClockSize(), s.getClockShellLoc());
        this._clockButton.addAltSprite(new ImageIcon(sheet.getSubimage(s.getClockPlaySheetLoc()[0] * this.getScale(), s.getClockPlaySheetLoc()[1] * this.getScale(), s.getClockSize()[0] * this.getScale(), s.getClockSize()[1] * this.getScale())), "2");
        this.setShellComponent(sheet, this._saveButton, s.getSaveSheetLoc(), s.getSaveRolloverSheetLoc(), s.getSaveSize(), s.getSaveShellLoc());
        this.setShellComponent(sheet, this._statusButton, s.getStatusSheetLoc(), s.getStatusRolloverSheetLoc(), s.getStatusSize(), s.getStatusShellLoc());
        this.setShellComponent(sheet, this._feedButton, s.getFeedSheetLoc(), s.getFeedRolloverSheetLoc(), s.getFeedSize(), s.getFeedShellLoc());
        this.setShellComponent(sheet, this._digisoulButton, s.getDigicoreSheetLoc(), s.getDigicoreRolloverSheetLoc(), s.getDigicoreSize(), s.getDigicoreShellLoc());
        this.setShellComponent(sheet, this._gameButton, s.getGameSheetLoc(), s.getGameRolloverSheetLoc(), s.getGameSize(), s.getGameShellLoc());
        this.setShellComponent(sheet, this._battleButton, s.getBattleSheetLoc(), s.getBattleRolloverSheetLoc(), s.getBattleSize(), s.getBattleShellLoc());
        this.setShellComponent(sheet, this._washButton, s.getWashSheetLoc(), s.getWashRolloverSheetLoc(), s.getWashSize(), s.getWashShellLoc());
        this.setShellComponent(sheet, this._lightButton, s.getLightSheetLoc(), s.getLightRolloverSheetLoc(), s.getLightSize(), s.getLightShellLoc());
        this.setShellComponent(sheet, this._firstAidButton, s.getFirstAidSheetLoc(), s.getFirstAidRolloverSheetLoc(), s.getFirstAidSize(), s.getFirstAidShellLoc());
        this.setShellComponent(sheet, this._tempButton, s.getTempSheetLoc(), s.getTempRolloverSheetLoc(), s.getTempSize(), s.getTempShellLoc());
        this.setShellComponent(sheet, this._callIcon, s.getCallSheetLoc(), s.getCallRolloverSheetLoc(), s.getCallSize(), s.getCallShellLoc());
        this.setSizes(s);
    }

    private void setShellComponent(BufferedImage sheet, SpriteObj o, int[] loc, int[] loc2, int[] size, int[] shellLoc) {
        if (loc != null && size != null && shellLoc != null) {
            o.getAltSprites().clear();
            ImageIcon i = new ImageIcon(sheet.getSubimage(loc[0] * this.getScale(), loc[1] * this.getScale(), size[0] * this.getScale(), size[1] * this.getScale()));
            o.setIcon(i);
            o.addAltSprite(i, "0");
            if (loc2 != null) {
                o.addAltSprite(new ImageIcon(sheet.getSubimage(loc2[0] * this.getScale(), loc2[1] * this.getScale(), size[0] * this.getScale(), size[1] * this.getScale())), "1");
            }
            o.setSize(size[0], size[1]);
            o.setLoc(shellLoc[0], shellLoc[1]);
        }
    }

    private boolean isIdle(PhysicalState myDigimon, Enum.Menu currentMenu) {
        return currentMenu == Enum.Menu.None && Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentAnim) && myDigimon.getAlive();
    }

    public void checkCall(PhysicalState myDigimon, Enum.Menu currentMenu) {
        if (myDigimon.getDisciplineCall() || myDigimon.checkCall()) {
            if (this.isIdle(myDigimon, currentMenu) && myDigimon.callMinutesLessThan(myDigimon.scaleToClock(Config._minutesToDisableCallSound))) {
                if (this._controller.getModel().getSettings().isFocus()) {
                    this.requestFocus();
                }
                this._sounds.playSound(SoundConfig._call);
            }
            if (!currentMenu.equals((Object)Enum.Menu.EvolutionTree) && !currentMenu.equals((Object)Enum.Menu.Settings)) {
                this._callIcon.setAltIcon(1);
            } else {
                this._callIcon.setAltIcon(0);
            }
        } else {
            this._callIcon.setAltIcon(0);
        }
    }

    private void checkClock() {
        this.setTime();
        this.checkTemp();
        this._tempLabel.setVisible(true);
        this.checkTime();
        this.checkSeason();
        this.setTicBarSize();
        this._ticBar.setVisible(true);
    }

    private void setTime() {
        this._hoursPane.setText(this.getExtraZero(Integer.toString(this._controller.getModel().getTime().getHours())));
        this._minutesPane.setText(this.getExtraZero(Integer.toString(this._controller.getModel().getTime().getMinutes())));
    }

    private void endSpecialIdleAnim() {
        this.resetAnimVars();
        this._currentAnim = Enum.State.Idling;
    }

    private void resetAnimVars() {
        this._animValue = 0;
        this._animValue2 = 0;
        this._animValue3 = 0;
        this._animValue4 = 0;
        this.getContentPane().repaint();
        this._frame = this._interval * -1;
    }

    public void endAnim() {
        this.resetAnimVars();
        PhysicalState digimon = this._controller.getModel().getDigimon();
        ArrayList animQueue = digimon.getAnimQueue();
        digimon.setCurrentState(Enum.State.Idling);
        if (!animQueue.isEmpty()) {
            this._currentAnim = (Enum.State)((Object)animQueue.get(0));
            animQueue.remove(0);
            animQueue.trimToSize();
            digimon.setStateNoRepeat(this._currentAnim);
        } else {
            this._currentAnim = Enum.State.None;
        }
    }

    private void awakeIdleDefault(boolean isAsleep) {
        if (!isAsleep) {
            this._emotionLabel.setVisible(false);
            this._itemLabel.setVisible(false);
            this.setSpriteCharDefaultY();
        }
    }

    private void idle(boolean currentAnimContainsIdle, boolean currentStateContainsIdle) {
        PhysicalState myDigimon = this._controller.getModel().getDigimon();
        boolean isUnwell = this._controller.setIdleType();
        if (myDigimon.getCurrentState() != this._currentAnim && !currentStateContainsIdle) {
            this.disableExtraLabels();
            this._currentAnim = null;
            this._frame = this._interval * -1;
        }
        if (currentAnimContainsIdle) {
            this.stateAnims(myDigimon, isUnwell);
        }
        if (this._controller.isPlaying() && myDigimon.getAlive() && this._currentAnim != null && this._currentAnim != Enum.State.None) {
            this.checkSpecialIdleAnim(isUnwell);
            switch (this._currentAnim) {
                case PoopDance: {
                    this.poopDance();
                    break;
                }
                case Yawning: {
                    this.yawning();
                    break;
                }
                case Weathering: {
                    this.weathering();
                    break;
                }
                case Surprising: {
                    this.surprising();
                    break;
                }
                case Tantrum: {
                    this.tantrum();
                    break;
                }
                case Personality_Happy: {
                    this.personalityMooding(Enum.Mood.Happy);
                    break;
                }
                case Personality_Angry: {
                    this.personalityMooding(Enum.Mood.Unhappy);
                    break;
                }
                case Idling: {
                    if (myDigimon.getAsleep()) {
                        if (myDigimon.getLights() && myDigimon.isFuton()) {
                            this.futonSleep(myDigimon.getEvolution().getDigimon(myDigimon.getIndex()), myDigimon.getNap());
                            break;
                        }
                        this.idleSleep(myDigimon);
                        break;
                    }
                    this.awakeIdleDefault(myDigimon.getAsleep());
                    if (myDigimon.getGrowthStage() == Enum.Stage.Egg) {
                        this.idleEgg();
                        break;
                    }
                    if (isUnwell || myDigimon.getWorld().getTravelSpeed() > 0 && myDigimon.isGeriatric()) {
                        this.checkIdleUnwell();
                        break;
                    }
                    this.checkIdleNormal();
                }
            }
        } else if (!this._controller.isPlaying()) {
            this.adjustCharacterForFilth();
            this.setFrozenIcon();
        } else if (!myDigimon.getAlive()) {
            this.adjustCharacterForFilth();
            this.setDeathIcon();
        }
    }

    private void stateAnims(PhysicalState myDigimon, boolean isUnwell) {
        this.checkStates(myDigimon);
        this.checkFilth(myDigimon);
        this.checkLights(myDigimon);
        this.stateNumTic(myDigimon, isUnwell);
    }

    private void stateNumTic(PhysicalState digimon, boolean isUnwell) {
        if (this._stateFrame % ((isUnwell ? 7 : (digimon.getAsleep() ? 10 : 7)) * this._interval) == 0) {
            this._stateNum = (byte)(this._stateNum + (this._stateNum > 0 ? -1 : 1));
            this._stateFrame = 0;
        }
    }

    private void checkStates(PhysicalState digimon) {
        if (this._select.isVisible() && this._currentAnim == Enum.State.Idling) {
            this.selectCharacter(digimon);
        }
        if (digimon.hasVitamin()) {
            this._vitaminState.setIcon(this._states.getSpriteSheet()[8 + this._stateNum]);
            this._vitaminState.setVisible(true);
        } else {
            this._vitaminState.setVisible(false);
        }
        if (digimon.isFatigued()) {
            this._fatigueState.setIcon(this._states.getSpriteSheet()[10 + this._stateNum]);
            this._fatigueState.setVisible(true);
        } else {
            this._fatigueState.setVisible(false);
        }
        if (digimon.isInj()) {
            this._injuryState.setIcon(this._states.getSpriteSheet()[2 + this._stateNum]);
            this._injuryState.setVisible(true);
        } else {
            this._injuryState.setVisible(false);
        }
        if (digimon.isSick()) {
            this._sickState.setIcon(this._states.getSpriteSheet()[6 + this._stateNum]);
            this._sickState.setVisible(true);
        } else {
            this._sickState.setVisible(false);
        }
        if (digimon.getBandage()) {
            this._bandageState.setIcon(this._states.getSpriteSheet()[0 + this._stateNum]);
            this._bandageState.setVisible(true);
        } else {
            this._bandageState.setVisible(false);
        }
        if (digimon.getMed()) {
            this._medicineState.setIcon(this._states.getSpriteSheet()[4 + this._stateNum]);
            this._medicineState.setVisible(true);
        } else {
            this._medicineState.setVisible(false);
        }
        if (Config._displayTeachingChance && digimon.getLights() && !digimon.getAsleep() && (digimon.getPraise() || digimon.getScold())) {
            this._teachState.setIcon(this._states.getSpriteSheet()[12 + this._stateNum]);
            this.setDynamicComponentLocation(this._teachState, this._character);
            this._teachState.setVisible(true);
        } else {
            this._teachState.setVisible(false);
        }
        if (this._fastClockDisplay.isVisible()) {
            if (this._animValue >= ViewConfig._hideFastClock) {
                this._fastClockDisplay.setVisible(false);
            } else {
                ++this._animValue;
            }
        }
    }

    private void setDynamicFastClockIcon(Enum.Menu m, int speed) {
        if (m == Enum.Menu.None && Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentAnim)) {
            this._animValue = 0;
            this.changeFastClockDisplayWidth(speed);
            this.setDynamicComponentLocation(this._fastClockDisplay, this._character);
            this._fastClockDisplay.setAltIcon("fastClock");
            this._fastClockDisplay.setVisible(true);
        }
    }

    private void setDynamicComponentLocation(SpriteObj o, SpriteObj c) {
        int mirrorLoc = (c.getLocX() - o.getWidth()) / this.getScale() - 3;
        int loc = (c.getLocX() + c.getSizeX()) / this.getScale() + 3;
        if (c.getIsMirror() && loc > this._mainDisplay.getWidth() || mirrorLoc > 0) {
            o.setLocX(mirrorLoc);
        } else {
            o.setLocX(loc);
        }
        o.setLocY(c.getLocY() / this.getScale());
    }

    private void checkFilth(PhysicalState digimon) {
        if (digimon.isFilth()) {
            this._filthLabel.setVisible(true);
            if (this._filthLabel.getAltSprites().isEmpty()) {
                this.drawFilthLevel(digimon.getFilth(), digimon.countFilth());
            }
            this.animFilth();
        }
    }

    private void animFilth() {
        if (this._stateNum == 0) {
            this._filthLabel.setAltIcon("filth");
        } else if (this._stateNum == 1) {
            this._filthLabel.setAltIcon("filth2");
        }
    }

    private void drawFilthLevel(byte[] filth, int count) {
        this._filthLabel.getAltSprites().clear();
        int width = 30;
        int height = 27;
        SpriteObj filthSheet = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "filth.png", null, 30, 27, 2, this.getScale());
        BufferedImage filth0 = null;
        BufferedImage filth1 = null;
        BufferedImage filth2 = null;
        BufferedImage filth3 = null;
        BufferedImage filth4 = null;
        BufferedImage filth5 = null;
        BufferedImage filth6 = null;
        BufferedImage filth7 = null;
        block19: for (byte b : filth) {
            switch (b) {
                case 1: {
                    if (filth0 != null) continue block19;
                    filth0 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[0]);
                    filth1 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[1]);
                    continue block19;
                }
                case 2: {
                    if (filth2 != null) continue block19;
                    filth2 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[2]);
                    filth3 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[3]);
                    continue block19;
                }
                case 3: {
                    if (filth4 != null) continue block19;
                    filth4 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[4]);
                    filth5 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[5]);
                    continue block19;
                }
                case 4: {
                    if (filth6 != null) continue block19;
                    filth6 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[6]);
                    filth7 = ViewUtil.createBuffImage(filthSheet.getSpriteSheet()[7]);
                }
            }
        }
        BufferedImage filthSpread = new BufferedImage(this._mainDisplay.getWidth(), this._mainDisplay.getHeight(), 2);
        Graphics2D g2 = filthSpread.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        BufferedImage filthSpread2 = new BufferedImage(this._mainDisplay.getWidth(), this._mainDisplay.getHeight(), 2);
        Graphics2D g22 = filthSpread2.createGraphics();
        oldColor = g22.getColor();
        g22.fillRect(0, 0, 0, 0);
        g22.setColor(oldColor);
        int bottom = this._mainDisplay.getHeight() / this.getScale() - height - 3;
        int top = bottom - height;
        int pad = 6;
        for (int i = 0; i < filth.length; ++i) {
            int x = 2;
            int y = bottom;
            switch (i) {
                case 1: {
                    y = top;
                    break;
                }
                case 2: {
                    x = width + pad;
                    y = bottom;
                    break;
                }
                case 3: {
                    x = width + pad;
                    y = top;
                    break;
                }
                case 4: {
                    x = width * 2;
                    x += pad * 2;
                    y = bottom;
                    break;
                }
                case 5: {
                    x = width * 2;
                    x += pad * 2;
                    y = top;
                }
            }
            x *= this.getScale();
            y *= this.getScale();
            BufferedImage first = null;
            BufferedImage second = null;
            switch (filth[i]) {
                case 1: {
                    first = filth0;
                    second = filth1;
                    break;
                }
                case 2: {
                    first = filth2;
                    second = filth3;
                    break;
                }
                case 3: {
                    first = filth4;
                    second = filth5;
                    break;
                }
                case 4: {
                    first = filth6;
                    second = filth7;
                }
            }
            g2.drawImage(first, null, x, y);
            g22.drawImage(second, null, x, y);
        }
        g2.dispose();
        g22.dispose();
        int filthWidth = (int)Math.ceil((double)count / 2.0);
        this._filthLabel.setSizeX(2 + filthWidth * 30 + pad * (filthWidth - 1));
        this._filthLabel.addAltSprite(new ImageIcon(filthSpread), "filth");
        this._filthLabel.addAltSprite(new ImageIcon(filthSpread2), "filth2");
        this._filthLabel.setAltIcon("filth");
        this._filthLabel.setVisible(true);
        filthSheet.dispose();
    }

    private void checkLights(PhysicalState myDigimon) {
        if (!myDigimon.getLights() && !myDigimon.getAsleep() || !myDigimon.getLights() && myDigimon.isPaused()) {
            this._roomEffect.setVisible(true);
            this._roomEffect.setAltIcon("lightsOff");
        } else if (myDigimon.getLights() && myDigimon.getAsleep()) {
            this._roomEffect.setVisible(false);
        } else if (myDigimon.getLights() && !myDigimon.getAsleep()) {
            this._roomEffect.setVisible(false);
        }
    }

    private void checkIdleNormal() {
        this._character.setVisible(true);
        byte travelSpeed = this._controller.getModel().getDigimon().getWorld().getTravelSpeed();
        switch (travelSpeed) {
            case 0: {
                this.idleNormal(this.getSpriteNum());
                break;
            }
            case 1: {
                this.idleWalk(this.getSpriteNum());
                break;
            }
            case 2: {
                this.idleRun(this.getSpriteNum());
            }
        }
    }

    private int checkMoodFrame(PhysicalState digimon, boolean forceFatigue) {
        int frameInc = 8;
        Random ran = new Random();
        int b = digimon.getExerciseLimit() + 1 - digimon.getExercise();
        int mod = ran.nextInt(b > 0 ? b : 1);
        if (!(!forceFatigue && digimon.getEnergy() > 0 && mod >= 3 || !digimon.isFatigued() && digimon.getExercise() <= Config._fullStrength && digimon.isFullyRecovered() || digimon.checkCall())) {
            frameInc = mod == 0 ? 10 : (mod == 1 ? 9 : (mod == 2 ? 4 : 2));
        } else if (digimon.getCurrentMood() == Enum.Mood.Unhappy || digimon.checkCall() || digimon.checkIdealTemp() == Enum.Mood.Unhappy) {
            mod = ran.nextInt(3);
            frameInc = mod == 0 ? 4 : 6;
        } else {
            mod = ran.nextInt(3);
            if (mod > 0) {
                if (digimon.getCurrentMood() == Enum.Mood.Happy) {
                    frameInc = 5;
                }
                if ((mod = ran.nextInt(12)) == 1 || mod == 0) {
                    Habitat h = digimon.getCurrentHabitat();
                    if (digimon.incompatibleElement(digimon.getElement(), h) || digimon.incompatibleField(digimon.getField(), h)) {
                        if (mod == 0) {
                            frameInc = 4;
                        } else if (mod == 1) {
                            frameInc = 6;
                        }
                    }
                }
            }
        }
        return frameInc;
    }

    private void stepFrame(int spriteNum) {
        boolean fatigueCheck;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        boolean geriatric = digimon.isGeriatric();
        boolean isRight = this._character.getIsMirror();
        int filthPad = 0;
        try {
            filthPad = this._filthLabel.getSizeX();
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
        int num = spriteNum + (geriatric ? 9 : 0);
        int currentNum = this._character.getSpriteNum();
        Random ran = new Random();
        int prob = ran.nextInt(100);
        int effectiveEnthusiasm = (int)(10.0 * ((double)digimon.getEnthusiasm() / (double)Config._maxEnthusiasm));
        boolean enthusiasmCheck = prob < 20 + effectiveEnthusiasm * 2;
        boolean bl = fatigueCheck = prob < 20 + effectiveEnthusiasm * 2 + (digimon.getExercise() > Config._fullStrength ? digimon.getExercise() * 2 : 0);
        if (this._character.getLocX() >= this._mainDisplay.getWidth() + filthPad - this._character.getSizeX() && isRight || this._character.getLocX() <= filthPad && !isRight) {
            if (prob < 50 + (effectiveEnthusiasm < 0 ? (int)Math.floor(effectiveEnthusiasm * 2) : effectiveEnthusiasm)) {
                num = currentNum == spriteNum || currentNum == spriteNum + 1 ? spriteNum + this.checkMoodFrame(digimon, false) : spriteNum + 1;
            } else {
                isRight = !isRight;
            }
        } else if ((double)prob > 10.0 + (40.0 - (double)(effectiveEnthusiasm * 2)) * (1.0 - (double)digimon.getEnergy() / (double)digimon.getMaxEnergy())) {
            num = currentNum == spriteNum + 1 ? spriteNum + (geriatric ? 9 : 0) : spriteNum + 1;
            if ((currentNum == spriteNum || currentNum == spriteNum + 1) && prob >= 0 && (enthusiasmCheck || fatigueCheck)) {
                num = spriteNum + this.checkMoodFrame(digimon, !enthusiasmCheck);
            } else if (enthusiasmCheck && prob <= 26 + effectiveEnthusiasm * 2) {
                isRight = !isRight;
            } else if ((num == 0 || num == 9 && geriatric) && this._character.getSpriteNum() == 1 || num == 1 && (this._character.getSpriteNum() == 0 || this._character.getSpriteNum() == 9 && geriatric)) {
                if (isRight) {
                    this._character.moveRight(3);
                } else {
                    this._character.moveLeft(3);
                }
            }
        } else {
            if ((currentNum == spriteNum || currentNum == spriteNum + 1) && prob >= 0 && (enthusiasmCheck || fatigueCheck)) {
                num = spriteNum + this.checkMoodFrame(digimon, !enthusiasmCheck);
            } else {
                int n = num = this._character.getSpriteNum() == 0 ? 1 : 0;
            }
            if (enthusiasmCheck) {
                isRight = prob % (effectiveEnthusiasm < 0 ? 2 * effectiveEnthusiasm : 2) == 0;
            }
        }
        this._character.drawNumMirror(num, isRight);
    }

    private void adjustCharacterForFilth() {
        if (this._filthLabel.getSizeX() > 0 && this._character.getLocX() < this._filthLabel.getSizeX() + this._filthLabel.getLocX()) {
            this.setSpriteCharDefault();
            this._character.setLocX(this._filthLabel.getSizeX() / this.getScale() + this._filthLabel.getLocX() / this.getScale());
            this.adjustEmotionLabel();
        }
    }

    private void idleNormal(int spriteNum) {
        this.adjustCharacterForFilth();
        if (this._frame >= this._interval * 0) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            int restless = digimon.getEnergy() > 0 ? digimon.getRestless() : -1;
            this.stepFrame(spriteNum);
            this._frame = this._interval * -(restless > 0 ? 5 : (restless < 0 ? 7 : 6));
        }
    }

    private void checkSpecialIdleAnim(boolean isUnwell) {
        block13: {
            int prob;
            PhysicalState digimon;
            block16: {
                block15: {
                    block14: {
                        digimon = this._controller.getModel().getDigimon();
                        if (!digimon.getAlive() || digimon.getGrowthStage() == Enum.Stage.Egg || digimon.getCurrentState() != Enum.State.Idling || this._currentAnim != Enum.State.Idling || digimon.getAsleep()) break block13;
                        if (!this._weather.getThunder()) break block14;
                        this._frame = -1;
                        this._currentAnim = Enum.State.Surprising;
                        break block13;
                    }
                    Random random = new Random();
                    prob = random.nextInt(1500);
                    if (prob != 10) break block15;
                    boolean isSleep = false;
                    boolean isWeather = false;
                    boolean poop = false;
                    if (!digimon.getAsleep() && digimon.sleepNotNap()) {
                        isSleep = true;
                    }
                    if (digimon.getCurrentWeather() != Enum.Weather.Clear && digimon.getCurrentWeather() != Enum.Weather.Cloudy) {
                        isWeather = true;
                    }
                    if (digimon.getBMGauge() >= digimon.getBMMax()) {
                        poop = true;
                    }
                    if (isSleep || isWeather || poop) {
                        ArrayList<Enum.State> states = new ArrayList<Enum.State>();
                        if (isSleep) {
                            states.add(Enum.State.Yawning);
                        }
                        if (isWeather) {
                            states.add(Enum.State.Weathering);
                        }
                        if (poop) {
                            states.add(Enum.State.PoopDance);
                        }
                        this._frame = -1;
                        this._currentAnim = (Enum.State)((Object)states.get(random.nextInt(states.size())));
                    }
                    break block13;
                }
                if (prob != 1 || digimon.getWorld().getTravelSpeed() != 0 || digimon.getEnergy() < digimon.getMaxEnergy() / 3 || digimon.getEnthusiasm() < 0 || digimon.getExercise() > digimon.getExerciseLimit() / 2 || isUnwell) break block16;
                switch (digimon.getCurrentMood()) {
                    case Happy: {
                        this._frame = -1;
                        this._currentAnim = Enum.State.Personality_Happy;
                        break block13;
                    }
                    case Neutral: 
                    case None: {
                        break block13;
                    }
                    case Unhappy: 
                    case Depressed: {
                        this._frame = -1;
                        this._currentAnim = Enum.State.Personality_Angry;
                        break block13;
                    }
                    default: {
                        throw new AssertionError((Object)digimon.getCurrentMood().name());
                    }
                }
            }
            if (prob % 500 == 0 && digimon.getDisciplineCall()) {
                this._frame = -1;
                this._currentAnim = Enum.State.Tantrum;
            }
        }
    }

    private int getTiredTravelSprite() {
        if (Utility.randomChance(this._controller.getModel().getDigimon().getWorld().getEnergyDecPercent(), 100)) {
            return 9;
        }
        return 0;
    }

    private void idleWalk(int spriteNum) {
        boolean isRight = this._controller.getModel().getDigimon().getWorld().getTravelRight();
        if (this._frame == this._interval * 0) {
            if (isRight) {
                this._character.moveRight(3);
            } else {
                this._character.moveLeft(3);
            }
            this._character.drawNumMirror(spriteNum, isRight);
        } else if (this._frame >= this._interval * 5) {
            if (isRight) {
                this._character.moveRight(3);
            } else {
                this._character.moveLeft(3);
            }
            this._character.drawNumMirror(this.getTiredTravelSprite() + 1, isRight);
            this._frame = this._interval * -5;
        }
        if (!isRight && this._character.getLocX() + this._character.getSizeX() <= -this._character.getSizeX()) {
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() + this._character.getSizeX() / this.getScale());
        } else if (isRight && this._character.getLocX() + this._character.getSizeX() >= this._mainDisplay.getWidth() + this._character.getSizeX()) {
            this._character.setLocX(-(this._character.getSizeX() / this.getScale()) - this._character.getSizeX() / this.getScale());
        }
    }

    private void idleRun(int spriteNum) {
        boolean isRight = this._controller.getModel().getDigimon().getWorld().getTravelRight();
        if (this._frame == this._interval * -7) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(spriteNum, isRight);
        } else if (this._frame == this._interval * -6) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(this.getTiredTravelSprite() + 1, isRight);
        } else if (this._frame == this._interval * -5) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(spriteNum, isRight);
        } else if (this._frame == this._interval * -4) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(this.getTiredTravelSprite() + 1, isRight);
        } else if (this._frame == this._interval * -3) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(spriteNum, isRight);
        } else if (this._frame == this._interval * -2) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(this.getTiredTravelSprite() + 1, isRight);
        } else if (this._frame == this._interval * -1) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(spriteNum, isRight);
        } else if (this._frame >= this._interval * 0) {
            if (isRight) {
                this._character.moveRight(6);
            } else {
                this._character.moveLeft(6);
            }
            this._character.drawNumMirror(this.getTiredTravelSprite() + 1, isRight);
            this._frame = -6 * this._interval;
        }
        if (!isRight && this._character.getLocX() + this._character.getSizeX() <= -this._character.getSizeX()) {
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() + this._character.getSizeX() / this.getScale());
        } else if (isRight && this._character.getLocX() + this._character.getSizeX() >= this._mainDisplay.getWidth() + this._character.getSizeX()) {
            this._character.setLocX(-(this._character.getSizeX() / this.getScale()) - this._character.getSizeX() / this.getScale());
        }
    }

    private void checkIdleUnwell() {
        this._character.setVisible(true);
        byte travelSpeed = this._controller.getModel().getDigimon().getWorld().getTravelSpeed();
        switch (travelSpeed) {
            case 0: {
                this.idleUnwell(this.getSpriteNum());
                break;
            }
            case 1: {
                this.idleUnwellWalk(this.getSpriteNum());
                break;
            }
            case 2: {
                this.idleUnwellRun(this.getSpriteNum());
            }
        }
    }

    private void idleUnwell(int spriteNum) {
        if (this._frame <= this._interval * 0) {
            this.setSpriteCharDefaultY();
            this._character.drawNumMirror(spriteNum + 10, false);
            this.adjustCharacterForFilth();
            this._frame = 25 * this._interval;
        } else if (this._frame == 25 * this._interval) {
            this._character.drawNumMirror(spriteNum + 10, false);
        } else if (this._frame == this._interval * 30) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 35) {
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 40) {
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 45) {
            this._character.moveLeft(1);
        } else if (this._frame >= this._interval * 50) {
            this._character.drawNumMirror(spriteNum + 9, false);
            this._frame = 0;
        }
    }

    private void idleUnwellWalk(int spriteNum) {
        boolean isRight = this._controller.getModel().getDigimon().getWorld().getTravelRight();
        if (this._frame == this._interval * 0) {
            if (isRight) {
                this._character.moveRight(3);
            } else {
                this._character.moveLeft(3);
            }
            this._character.drawNumMirror(spriteNum + 9, isRight);
        } else if (this._frame >= this._interval * 14) {
            if (isRight) {
                this._character.moveRight(3);
            } else {
                this._character.moveLeft(3);
            }
            this._character.drawNumMirror(spriteNum + 10, isRight);
            this._frame = this._interval * -14;
        }
        if (this._character.getLocX() + this._character.getSizeX() <= -this._character.getSizeX()) {
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() + this._character.getSizeX() / this.getScale());
        }
    }

    private void idleUnwellRun(int spriteNum) {
        boolean isRight = this._controller.getModel().getDigimon().getWorld().getTravelRight();
        if (this._frame == this._interval * 0) {
            if (isRight) {
                this._character.moveRight(3);
            } else {
                this._character.moveLeft(3);
            }
            this._character.drawNumMirror(spriteNum + 9, isRight);
        } else if (this._frame >= this._interval * 7) {
            if (isRight) {
                this._character.moveRight(3);
            } else {
                this._character.moveLeft(3);
            }
            this._character.drawNumMirror(spriteNum + 10, isRight);
            this._frame = this._interval * -7;
        }
        if (this._character.getLocX() + this._character.getSizeX() <= -this._character.getSizeX()) {
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() + this._character.getSizeX() / this.getScale());
        }
    }

    private void idleEgg() {
        this.adjustCharacterForFilth();
        if (this._frame == this._interval * 0) {
            this._character.drawNumMirror(0, false);
        } else if (this._frame == this._interval * 5) {
            this._character.drawNumMirror(1, false);
            this._frame = -5 * this._interval;
        }
    }

    private void idleSleep(PhysicalState digimon) {
        SpriteObj o;
        boolean nap = digimon.getNap();
        boolean lights = digimon.getLights();
        SpriteObj spriteObj = o = lights ? this._emotionLabel : this._roomEffect;
        if (this._frame <= this._interval * 0) {
            this.setSpriteCharDefault();
            this.adjustCharacterForFilth();
            this._frame = 0;
            this._emotionLabel.setVisible(lights);
            this._roomEffect.setVisible(!lights);
            this._character.setVisible(!lights);
            this._character.drawNumMirror(2, false);
            o.setAltIcon(this.getLightsSprites(nap, lights)[0]);
        } else if (this._frame == this._interval * 10) {
            this._character.drawNumMirror(3, false);
            o.setAltIcon(this.getLightsSprites(nap ? !Utility.randomChance((int)((double)digimon.getNapToSleepPercent() * Config._napToSleepIndicatorChanceCoefficient), 100) : nap, lights)[1]);
        } else if (this._frame >= this._interval * 20) {
            this._character.drawNumMirror(2, false);
            o.setAltIcon(this.getLightsSprites(nap, lights)[0]);
            this._frame = -1;
        }
    }

    private String[] getLightsSprites(boolean nap, boolean lights) {
        if (lights) {
            return new String[]{nap ? "napLights" : "sleepLights", nap ? "napLights2" : "sleepLights2"};
        }
        return new String[]{nap ? "napLightsOff" : "sleepLightsOff", nap ? "napLightsOff2" : "sleepLightsOff2"};
    }

    private void hatch() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.checkFilth(digimon);
        this.stateNumTic(digimon, false);
        if (this._frame <= 0) {
            this._controller.slowClock();
            this._stateNum = 0;
            this.setSpriteCharDefault();
            this.adjustCharacterForFilth();
            this._character.setVisible(true);
            this._character.drawNumMirror(0, false);
            this._frame = 0;
        } else if (this._frame == this._interval * 4) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 5) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._hatch);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 7) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 8) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 9) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 10) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 11) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 12) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 13) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 14) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 15) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 16) {
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 19) {
            this._character.drawNumMirror(2, false);
        } else if (this._frame >= this._interval * 29) {
            if (this._controller.getModel().getDigimon().checkEvol(-1, -1, false, false)) {
                this.getCharSprite();
                this.setSpriteCharDefault();
            }
            this.endAnim();
        }
    }

    private void poopOutsideMove() {
        boolean walking;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        boolean left = digimon.getWorld().getTravelRight();
        boolean bl = left ? this._character.getLocX() > -this._character.getSizeX() - 18 * this.getScale() : (walking = this._character.getLocX() < this._mainDisplay.getWidth() + 18 * this.getScale());
        if (this._frame <= 0) {
            this._frame = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.setVisible(true);
        } else if (this._frame % (this._interval * 2) == 0) {
            if (walking) {
                int currentNum = this._character.getSpriteNum();
                int num = currentNum == 0 ? 4 : 0;
                if (left) {
                    this._character.moveLeft(6);
                } else {
                    this._character.moveRight(6);
                }
                this._character.drawNumMirror(num, !left);
            } else {
                this._frame = -1;
                this._currentAnim = Enum.State.Pooping_Outside;
                this.poopOutside();
            }
        }
    }

    private void playPoopSound(byte f) {
        if (f == 1) {
            this._sounds.playSound(SoundConfig._smallPoop);
        } else if (f > 2) {
            this._sounds.playSound(SoundConfig._largePoop);
        } else {
            this._sounds.playSound(SoundConfig._poop);
        }
    }

    private void poopOutside() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
        } else if (this._frame == this._interval * 12) {
            this.playPoopSound(this._controller.getModel().getDigimon().poop(false));
        } else if (this._frame == this._interval * 24) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            if (digimon.getTournament().getActive() || digimon.getWorld().getCurrentZone().isTown() != null) {
                digimon.cleanMoodIncrease();
                this._sounds.playSound(SoundConfig._flush);
            }
        } else if (this._frame == this._interval * 36) {
            this._frame = -1;
            this._currentAnim = Enum.State.Pooping_Outside_Return;
            this.poopOutsideReturn();
        }
    }

    private void poopOutsideReturn() {
        boolean walking;
        boolean left;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        boolean bl = left = !digimon.getWorld().getTravelRight();
        boolean bl2 = left ? this._character.getLocX() > (55 - this._xPad) * this.getScale() : (walking = this._character.getLocX() < (55 - this._xPad) * this.getScale());
        if (this._frame <= 0) {
            this._frame = 0;
        } else if (this._frame % (this._interval * 1) == 0) {
            if (walking) {
                int currentNum = this._character.getSpriteNum();
                int num = currentNum == 0 ? 1 : 0;
                if (left) {
                    this._character.moveLeft(3);
                } else {
                    this._character.moveRight(3);
                }
                this._character.drawNumMirror(num, !left);
            } else {
                this.endAnim();
            }
        }
    }

    private void poopDance() {
        if (this._frame <= 0) {
            this._frame = 0;
            this._character.drawNum(0);
        } else if (this._frame == this._interval * 2) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 4) {
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 6) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 8) {
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 10) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 12) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 14) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 16) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 18) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * 20) {
            this.endSpecialIdleAnim();
        }
        this._character.setVisible(true);
    }

    private void poop() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.checkFilth(digimon);
        this.stateNumTic(digimon, false);
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this._stateNum = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.setLocX(0);
            this.adjustCharacterForFilth();
            if (digimon.countFilth() % 2 == 0) {
                this._character.moveRight(30);
            }
            this._character.setVisible(true);
            this._character.drawNumMirror(this.getSpriteNum() + 4, true);
        } else if (this._frame == this._interval * 3) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 6) {
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 9) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 12) {
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 15) {
            this._character.moveLeft(1);
        } else if (this._frame == this._interval * 18) {
            this._character.moveRight(1);
            byte f = digimon.poop(false);
            this.drawFilthLevel(digimon.getFilth(), digimon.countFilth());
            this.adjustCharacterForFilth();
            this.playPoopSound(f);
            this._character.drawNumMirror(this.getSpriteNum() + 5, true);
        } else if (this._frame == this._interval * 24) {
            this._filthLabel.getAltSprites().clear();
            this.endAnim();
        }
    }

    private void evolFinish(boolean evolved) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._character.setVisible(true);
        this._roomEffect.removeIcon();
        if (digimon.getGrowthStage() != Enum.Stage.Egg) {
            if (evolved) {
                digimon.checkUnlockItem();
                this._controller.setJogressPartner(null);
                this._jogressMatch = "";
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        } else {
            this._controller.leaveTourney(digimon);
        }
    }

    private void itemEvolve() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this._itemLabel.setLocX(27 - this._xPad);
            this.setItemSet();
            this._character.setVisible(true);
            this._battleFlash.removeIcon();
            this._battleFlash.setVisible(false);
            this._longClip = this._sounds.loopSound(SoundConfig._itemEvolveLoop, SoundConfig._masterVolume);
            this._character.drawNumMirror(this._animValue + 4, false);
            this._character.setLocX(81 - this._xPad);
            this._itemLabel.setLoc(3, 62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(this._animValue + 1, false);
            this._itemLabel.setVisible(true);
            this._foodLabel.setVisible(false);
        } else if (this._frame == this._interval * 2) {
            this._character.drawNumMirror(this._animValue + 1, false);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 4) {
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 6) {
            this._character.drawNumMirror(this._animValue + 4, false);
            this._itemLabel.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 8) {
            this._itemLabel.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 10) {
            this._character.drawNumMirror(this._animValue + 1, false);
            this._itemLabel.drawNumMirror(6, false);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.drawNumMirror(7, false);
        } else if (this._frame == this._interval * 14) {
            this._character.drawNumMirror(this._animValue + 4, false);
            this._itemLabel.drawNumMirror(8, false);
        } else if (this._frame == this._interval * 17) {
            this._character.moveLeft(3);
            this._itemLabel.moveLeft(3);
        } else if (this._frame >= this._interval * 18 && this._frame <= this._interval * 25 && this._frame % (1 * this._interval) == 0) {
            this._character.moveLeft(3);
            this._itemLabel.moveLeft(3);
        } else if (this._frame == this._interval * 28) {
            this._foodLabel.setLoc(this._itemLabel.getSizeX() / this.getScale() / 2 + this._itemLabel.getLocX() / this.getScale(), this._itemLabel.getLocY() / this.getScale());
            this._foodLabel.setSize(48, 48);
            this._foodLabel.setIcon(ViewUtil.flipIcon(this._itemLabel.getSpriteSheet()[this._itemLabel.getSpriteNum()]));
            this._foodLabel.setVisible(true);
            this._foodLabel.moveRight(4);
        } else if (this._frame >= this._interval * 29 && this._frame <= this._interval * 47 && this._frame % (1 * this._interval) == 0) {
            this._foodLabel.moveRight(4);
        } else if (this._frame >= this._interval * 50 && this._frame <= 63 * this._interval && this._frame % (3 * this._interval) == 0) {
            this._character.drawNumMirror(this._animValue + this._character.getSpriteNum() == 6 ? 4 : 6, false);
        } else if (this._frame == this._interval * 68) {
            this._foodLabel.setLocX(this._character.getLocX() / this.getScale());
            this._itemLabel.setLocX(this._character.getLocX() / this.getScale());
        } else if (this._frame == this._interval * 69) {
            this.disposeMusic();
            this._itemLabel.setVisible(false);
            this.setSpriteCharDefault();
            this.endAnim();
            this._controller.getModel().getDigimon().setCurrentState(Enum.State.Evolving);
        }
    }

    private boolean jogressPartOne(int start, int end, boolean isLeft, SpriteObj o) {
        int l;
        int n = l = isLeft ? 1 : -1;
        if (this._frame >= start * this._interval && this._frame < (end - 2) * this._interval && this._frame % this._interval == 0) {
            o.moveLeft(6 * l);
            return false;
        }
        if (this._frame == end * this._interval) {
            o.moveLeft(6 * l);
            o.drawNumMirror(6, !isLeft);
            return false;
        }
        return this._frame > end * this._interval;
    }

    private void jogress() {
        int end = 19;
        int partOneEnd = end * 2 + 21;
        if (this._frame <= 0) {
            this._controller.slowClock();
            this._longClip = this._sounds.loopSound(SoundConfig._jogressLoop, SoundConfig._masterVolume);
            this.resetScreen();
            this._frame = 0;
            this._character.setLocX(-2 + this._mainDisplay.getWidth() / this.getScale());
            this._opponent.setLocX(-4 - this._opponent.getSizeX() / this.getScale());
            this._opponent.setVisible(false);
            this._character.drawNumMirror(4, false);
            this._character.setVisible(true);
        } else if (this.jogressPartOne(1, end, true, this._character)) {
            if (this._frame == (end + 7) * this._interval) {
                this._roomEffect.setVisible(true);
                this._roomEffect.setAltIcon("lightsOff");
                this._character.setVisible(false);
            } else if (this._frame == (end + 10) * this._interval) {
                this._roomEffect.setVisible(false);
                this._opponent.setVisible(true);
                this._opponent.drawNumMirror(4, true);
            } else if (this.jogressPartOne(end + 11, end * 2 + 11, false, this._opponent)) {
                if (this._frame == (end * 2 + 18) * this._interval) {
                    this._roomEffect.setVisible(true);
                    this._opponent.setVisible(false);
                } else if (this._frame == (partOneEnd + 3) * this._interval) {
                    this._roomEffect.setVisible(false);
                    this._character.drawNumMirror(6, true);
                    this._character.setVisible(true);
                } else if (this._frame == (partOneEnd + 10) * this._interval) {
                    this._opponent.drawNumMirror(6, false);
                    this._opponent.setVisible(true);
                    this._character.setVisible(false);
                } else if (this._frame == (partOneEnd + 14) * this._interval) {
                    this._character.moveRight(12);
                    this._opponent.setVisible(false);
                    this._character.setVisible(true);
                } else if (this._frame == (partOneEnd + 18) * this._interval) {
                    this._opponent.moveLeft(12);
                    this._opponent.setVisible(true);
                    this._character.setVisible(false);
                } else if (this._frame == (partOneEnd + 20) * this._interval) {
                    this._character.moveRight(12);
                    this._opponent.setVisible(false);
                    this._character.setVisible(true);
                } else if (this._frame == (partOneEnd + 22) * this._interval) {
                    this._opponent.moveLeft(12);
                    this._opponent.setVisible(true);
                    this._character.setVisible(false);
                } else if (this._frame == (partOneEnd + 23) * this._interval) {
                    this._opponent.setVisible(false);
                    this._character.setVisible(true);
                } else if (this._frame == (partOneEnd + 24) * this._interval) {
                    this._opponent.setVisible(true);
                    this._character.setVisible(false);
                } else if (this._frame == (partOneEnd + 25) * this._interval) {
                    this._opponent.setVisible(false);
                    this._character.setVisible(true);
                } else if (this._frame == (partOneEnd + 26) * this._interval) {
                    this._opponent.setVisible(true);
                    this._character.setVisible(false);
                } else if (this._frame == (partOneEnd + 27) * this._interval) {
                    this._opponent.setVisible(false);
                    this._character.setVisible(true);
                } else if (this._frame == (partOneEnd + 28) * this._interval) {
                    this._opponent.setVisible(true);
                    this._character.setVisible(false);
                    this.disposeMusic();
                } else if (this._frame >= (partOneEnd + 29) * this._interval && this._frame < (partOneEnd + 29 + 35) * this._interval) {
                    this.evolveAnim(partOneEnd + 29);
                    if (this._frame < (partOneEnd + 29 + 21) * this._interval) {
                        this._opponent.setVisible(true);
                    }
                } else if (this._frame == (partOneEnd + 29 + 35 + 7) * this._interval) {
                    this.resetScreen();
                    this.evolFinish(true);
                }
            }
        }
        if (this._frame == (partOneEnd + 29 + 20) * this._interval) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            String[] j = this._jogressMatch.split(",");
            digimon.jogress(j[0], Integer.parseInt(j[1]));
        }
        if (this._frame == (partOneEnd + 29 + 21) * this._interval) {
            this._opponent.setVisible(false);
        }
    }

    private void digivolve() {
        this.evolveAnim();
        if (this._frame == this._interval * 41) {
            this.resetScreen();
            this.evolFinish(true);
        }
    }

    private void evolveAnim() {
        this.evolveAnim(0);
    }

    private void evolveAnim(int start) {
        if (this._frame <= this._interval * start) {
            this._controller.slowClock();
            this._frame = this._interval * start;
            this.disableMainMenu();
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.drawNum(0);
            this._character.setVisible(true);
            this._roomEffect.setVisible(true);
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * (start + 5)) {
            this._sounds.playSound(SoundConfig._evolve);
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * (start + 10)) {
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * (start + 12)) {
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * (start + 14)) {
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * (start + 19)) {
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * (start + 21)) {
            this.changeSprite();
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * (start + 25)) {
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * (start + 27)) {
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * (start + 29)) {
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * (start + 32)) {
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * (start + 34)) {
            this._roomEffect.setAltIcon("evol");
        }
    }

    public void changeSprite() {
        this.getCharSprite();
        this.setSpriteCharDefault();
    }

    private void teleportLeave() {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.setVisible(true);
            this._character.drawNumMirror(0, false);
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * 3) {
            this._sounds.playSound(SoundConfig._teleportDisappear);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 9) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 15) {
            this._sounds.playSound(SoundConfig._teleportDisappear);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 18) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 21) {
            this._sounds.playSound(SoundConfig._teleportDisappear);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 22) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 23) {
            this._roomEffect.setVisible(true);
            this._character.setVisible(false);
        } else if (this._frame >= this._interval * 26 && this._roomEffect.getSizeX() / this.getScale() > 3 && this._roomEffect.getSizeY() / this.getScale() > 3 && this._frame % 3 * this._interval == 0) {
            if (this._frame == this._interval * 26) {
                this._sounds.playSound(SoundConfig._teleportShrink);
            }
            this._roomEffect.setSize(this._roomEffect.getSizeX() / this.getScale() - 6, this._roomEffect.getSizeY() / this.getScale() - 2);
            this._roomEffect.setLoc(this._roomEffect.getLocX() / this.getScale() + 3, this._roomEffect.getLocX() / this.getScale());
        } else if (this._roomEffect.getSizeX() / this.getScale() <= 3 && this._roomEffect.getLocY() / this.getScale() > -this._roomEffect.getSizeY() / this.getScale() && this._frame % 2 * this._interval == 0) {
            if (this._frame == 206) {
                this._sounds.playSound(SoundConfig._teleportDepart);
            }
            this._roomEffect.setLocY(this._roomEffect.getLocY() / this.getScale() - 3);
        } else if (this._roomEffect.getSizeX() / this.getScale() <= 3 && this._roomEffect.getLocY() / this.getScale() <= -this._roomEffect.getSizeY() / this.getScale()) {
            this._currentAnim = Enum.State.Teleport_Arrive;
            this._frame = -1;
        }
    }

    private void teleportArrive() {
        if (this._frame <= 0 * this._interval) {
            this._frame = 0;
            PhysicalState digimon = this._controller.getModel().getDigimon();
            digimon.setIsHome(!this._controller.getModel().getDigimon().getIsHome());
            this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        } else if (this._roomEffect.getSizeX() / this.getScale() <= 3 && this._roomEffect.getLocY() / this.getScale() < this._mainDisplay.getSize().height / this.getScale() - this._roomEffect.getSizeY() / this.getScale() && this._frame % 2 * this._interval == 0) {
            if (this._frame == 2) {
                this._sounds.playSound(SoundConfig._teleportArrive);
            }
            this._roomEffect.setLocY(this._roomEffect.getLocY() / this.getScale() + 3);
        } else if (this._roomEffect.getSizeX() / this.getScale() != 105 && this._roomEffect.getLocY() / this.getScale() >= this._mainDisplay.getSize().height / this.getScale() - this._roomEffect.getSizeY() / this.getScale() && this._frame % 2 * this._interval == 0) {
            if (this._frame == 44) {
                this._sounds.playSound(SoundConfig._teleportExpand);
            }
            this._roomEffect.setSize(this._roomEffect.getSizeX() / this.getScale() + 6, this._roomEffect.getSizeY() / this.getScale() + 2);
            this._roomEffect.setLoc(this._roomEffect.getLocX() / this.getScale() - 3, this._roomEffect.getLocX() / this.getScale() - 3);
        } else if (this._roomEffect.getSizeX() / this.getScale() == 105 && this._roomEffect.getLocY() / this.getScale() >= 49 - this._yPad) {
            this.teleportAppear(94);
        }
    }

    private void teleportAppear(int frame) {
        if (this._frame == frame) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == frame + 1 * this._interval) {
            this._sounds.playSound(SoundConfig._teleportAppear);
            this._roomEffect.setVisible(true);
        } else if (this._frame == frame + 2 * this._interval) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == frame + 5 * this._interval) {
            this._sounds.playSound(SoundConfig._teleportAppear);
            this._roomEffect.setVisible(true);
        } else if (this._frame == frame + 8 * this._interval) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == frame + 14 * this._interval) {
            this._sounds.playSound(SoundConfig._teleportAppear);
            this._roomEffect.setVisible(true);
            this._character.setVisible(true);
        } else if (this._frame == frame + 20 * this._interval) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == frame + 23 * this._interval) {
            this._roomEffect.setSize(105, 60);
            this._roomEffect.setLocX(26 - this._xPad);
            this._roomEffect.setLocY(0);
            this.resetFilth();
            this.endAnim();
        }
    }

    private void retreatToTown() {
        if (this._frame <= 0 * this._interval) {
            this.setSpriteCharDefault();
            this._character.setVisible(true);
            this._character.drawNumMirror(9, false);
            this._animRect.changeColor(0, 0, 0, 0);
            this._animRect.setVisible(true);
            this._animValue = 0;
            this._animValue2 = 255;
            this._frame = 0;
        } else if (this._animValue < 255 && this._animValue2 == 255) {
            this._animValue += 5;
            if (this._animValue >= 255) {
                this._animValue = 255;
                this._backgroundAnim.checkBackNoAnim(this._controller.getModel().getDigimon(), this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
            }
            this._animRect.changeColor(0, 0, 0, this._animValue);
            this._overlay.repaint();
        } else if (this._animValue2 > 0 && this._animValue == 255) {
            this._animValue2 -= 5;
            if (this._animValue2 < 0) {
                this._animValue2 = 0;
            }
            this._animRect.changeColor(0, 0, 0, this._animValue2);
            this._overlay.repaint();
        } else if (this._animValue == 255 && this._animValue2 == 0) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            if (digimon.getWorld().getAdventureLife() == 0) {
                digimon.getWorld().setAdventureLife(3);
            }
            this.endAnim();
        }
    }

    private void pause(PhysicalState digimon) {
        this.checkFilth(digimon);
        this.stateNumTic(digimon, false);
        if (this._frame <= 0 * this._interval) {
            this.setSpriteCharDefault();
            this.adjustCharacterForFilth();
            this._character.setVisible(true);
            this._frame = 0;
        }
        this.fade(0);
        if (this._animValue >= 255 && this._animValue2 >= 255) {
            this._sounds.loopSound(SoundConfig._freezeLoop, 1);
            this._character.setIcon(this._frozen);
        } else if (this._animValue >= 255 && this._animValue2 <= 0) {
            this._controller.onPauseFinished();
            this.endAnim();
        }
    }

    private void unpause(PhysicalState digimon) {
        this.checkFilth(digimon);
        this.stateNumTic(digimon, false);
        if (this._frame <= 0 * this._interval) {
            this.disableMainMenu();
            this._roomEffect.setVisible(false);
            this._character.setVisible(true);
            this.setSpriteCharDefault();
            this.adjustCharacterForFilth();
            this._character.setIcon(this._frozen);
            this._frame = 0;
        }
        this.fade(0);
        if (this._animValue >= 255 && this._animValue2 >= 255) {
            this._sounds.loopSound(SoundConfig._unfreezeLoop, 1);
            this._character.drawNumMirror(this._controller.getModel().getDigimon().getGrowthStage() == Enum.Stage.Egg ? this._controller.getModel().getDigimon().getSpriteNum() : 0, false);
        } else if (this._animValue >= 255 && this._animValue2 <= 0) {
            this._controller.onUnpauseFinished();
            this.endAnim();
        }
        this._character.setVisible(true);
    }

    private void transportAnim(Enum.State anim, int id) {
        switch (anim) {
            case BirdraTransport: 
            case GarudaTransport: 
            case PhoenixTransport: {
                this.transport(anim, id);
                break;
            }
            case WhaTransport: {
                this.whaTransport();
            }
        }
    }

    private void whaTransport() {
        if (this._frame <= 0) {
            this.resetScreen();
            this._frame = 0;
            this._itemLabel.setVisible(false);
            this._character.drawNumMirror(1, false);
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() - this._character.getSizeX() / this.getScale() - 6);
            this._character.setVisible(true);
            EvolutionInfo mon = this._controller.getModel().getDigimon().getEvolution().getDigimon(193);
            this.setOppSprites(this.getOppSet(mon.getNewStage(), mon.getNewSpriteSet(), mon.getNewSpriteNum(), true));
            this._opponent.setSize(48, 48);
            this._opponent.setLoc(-((int)((double)(this._opponent.getSizeX() / this.getScale()) * 0.75)), this._mainDisplay.getHeight() / this.getScale() + this._opponent.getSizeY() / this.getScale() / 2);
            this._opponent.drawNumMirror(0, true);
            this._opponent.setVisible(false);
            this.setItemSet();
            this._itemLabel.drawNumMirror(0, false);
            this._itemLabel.setLocX(this._character.getLocX() / this.getScale() - 36);
            this._itemLabel.setLocY(-6);
        } else if (this._frame == this._interval * 5) {
            this._sounds.playSound(SoundConfig._whaTransportUseTicket);
            this._character.drawNumMirror(5, false);
            this._itemLabel.setVisible(true);
        } else if (this._frame == this._interval * 11) {
            this._character.drawNumMirror(0, false);
            this._itemLabel.setVisible(false);
            this._opponent.setVisible(true);
        } else if (this._frame >= 12 * this._interval && this._frame <= 21 * this._interval) {
            this._opponent.moveUp(1);
        } else if (this._frame >= 22 * this._interval && this._frame <= 26 * this._interval) {
            this._opponent.moveRight(1);
            if (this._frame % (2 * this._interval) == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() == 0 ? 1 : 0, true);
            }
        } else if (this._frame == 27 * this._interval) {
            this._character.drawNumMirror(1, false);
        } else if (this._frame == 32 * this._interval) {
            this._opponent.drawNumMirror(6, true);
            this._sounds.playSound(SoundConfig._whaTransportSurprise);
            this._opponent.moveUp(3);
        } else if (this._frame == 33 * this._interval) {
            this._opponent.moveUp(3);
            this._opponent.moveRight(3);
        } else if (this._frame == 34 * this._interval) {
            this._frame = 0;
            this._currentAnim = Enum.State.WhaTransportFade;
            this.whaTransportFade();
        }
    }

    private void whaTransportFade() {
        if (this._frame <= 0 * this._interval) {
            this._frame = 0;
            this._character.drawNumMirror(6, false);
            this._character.moveRight(1);
            this._character.moveUp(1);
            this._opponent.moveUp(3);
            this._opponent.moveRight(3);
        } else if (this._frame == 1 * this._interval) {
            this._character.moveRight(1);
            this._opponent.moveUp(3);
            this._opponent.moveRight(3);
        } else if (this._frame == 2 * this._interval) {
            this._character.moveDown(1);
            this._opponent.moveUp(3);
            this._opponent.moveRight(3);
        } else if (this._frame >= 3 * this._interval) {
            this.fade(3 * this._interval);
            if (this._animValue >= 255 && this._animValue2 == 255) {
                this._pauseWeather = true;
                this._weather.getOverlay().setVisible(false);
                PhysicalState digimon = this._controller.getModel().getDigimon();
                this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), (int)this._controller.getModel().getSettings().getGameScale(), this._controller.getBattle(), 8);
                this.setSpriteCharDefault();
                this._character.setVisible(false);
                this._opponent.setLoc(this._mainDisplay.getWidth() / this.getScale() + this._opponent.getSizeX() / this.getScale() / 2, this._character.getLocY() / this.getScale());
                this._opponent.moveUp(3);
                this._opponent.drawNumMirror(0, false);
            } else if (this._animValue >= 255 && this._animValue2 <= 0) {
                this._frame = 0;
                this._currentAnim = Enum.State.WhaTransportSwim;
                this.whaTransportSwim();
            }
        }
    }

    private void whaTransportSwim() {
        if (this._frame == 0) {
            if (this._opponent.getLocX() > -this._opponent.getSizeX() * 2) {
                this._opponent.moveLeft(6);
                if (this._frame % (2 * this._interval) == 0) {
                    if (this._opponent.getSpriteNum() == 0) {
                        this._opponent.drawNumMirror(1, false);
                        this._opponent.moveUp(2);
                    } else {
                        this._opponent.drawNumMirror(0, false);
                        this._opponent.moveDown(2);
                    }
                }
                this._frame = -1 * this._interval;
            } else {
                this.endAnim();
                this._controller.getModel().getDigimon().setPriorityState(Enum.State.WhaTransportArrive);
            }
        }
    }

    private void whaTransportArrive() {
        if (this._frame <= 0) {
            this._pauseWeather = false;
            this._frame = 0;
            PhysicalState digimon = this._controller.getModel().getDigimon();
            digimon.transport(Enum.State.WhaTransport, this.setMapPage(this._consumablePage, false).getMapNum());
            this.setupZones();
            this._backgroundAnim.resetDisplayedHabitat();
            this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
            this._character.setLocX(-this._character.getSizeX() / this.getScale());
            this._character.drawNumMirror(0, false, false);
            this._opponent.drawNumMirror(0, false);
            this._opponent.setVisible(true);
            this._opponent.setLoc(this._mainDisplay.getWidth() / this.getScale(), this._mainDisplay.getHeight() / this.getScale());
        } else if (this._frame >= 1 * this._interval && this._frame <= 7 * this._interval) {
            this._opponent.moveUp(1);
            this._opponent.moveLeft(1);
        } else if (this._frame == 13 * this._interval) {
            this._opponent.drawNumMirror(2, false);
            this._sounds.playSound(SoundConfig._whaTransportEject);
            this._character.setVisible(true);
            this._character.setLocY(this._opponent.getLocY() / this.getScale() - this._opponent.getSizeY() / this.getScale() + 21);
            this._character.setLocX(this._opponent.getLocX() / this.getScale() - 3);
            this._character.drawNumMirror(9, false);
        } else if (this._frame >= 14 * this._interval && this._frame <= 17 * this._interval) {
            this._character.moveUp(2);
            this._character.moveLeft(1);
        } else if (this._frame >= 17 * this._interval + 1 && this._frame <= 20 * this._interval) {
            this._character.moveUp(1);
            this._character.moveLeft(1);
        } else if (this._frame >= 20 * this._interval + 1 && this._frame <= 23 * this._interval) {
            this._character.moveDown(1);
            this._character.moveLeft(1);
        } else if (this._frame >= 23 * this._interval + 1 && this._frame <= 27 * this._interval) {
            this._character.moveDown(2);
            this._character.moveLeft(1);
        } else if (this._frame == 27 * this._interval + 1) {
            this._character.moveDown(3);
            this._sounds.playSound(SoundConfig._call);
            this._character.drawNumMirror(9, false);
        } else if (this._frame == 28 * this._interval) {
            this._character.moveUp(1);
            this._character.moveLeft(1);
        } else if (this._frame == 29 * this._interval) {
            this._sounds.playSound(SoundConfig._whaTransportFall);
            this._character.moveDown(1);
            this._character.moveLeft(1);
        } else if (this._frame == 30 * this._interval) {
            this._character.moveLeft(1);
            this._opponent.drawNumMirror(0, true);
        } else if (this._frame == 34 * this._interval) {
            this._character.drawNumMirror(0, true);
            this._opponent.drawNumMirror(1, true);
            this._opponent.moveRight(1);
        } else if (this._frame == 40 * this._interval) {
            this._sounds.playSound(SoundConfig._angry);
            this._character.drawNumMirror(4, true);
        } else if (this._frame == 46 * this._interval) {
            this._character.drawNumMirror(6, true);
        } else if (this._frame == 52 * this._interval) {
            this._character.drawNumMirror(4, true);
        } else if (this._frame == 58 * this._interval) {
            this._character.drawNumMirror(6, true);
        } else if (this._frame == 64 * this._interval) {
            this.endAnim();
        }
        if (this._frame >= 34 * this._interval && this._frame <= 64 * this._interval) {
            if (this._frame % (2 * this._interval) == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() == 0 ? 1 : 0, true);
            }
            this._opponent.moveRight(1);
        }
        if (this._frame == 15 * this._interval) {
            this._character.drawNumMirror(4, false);
        } else if (this._frame == 16 * this._interval) {
            this._opponent.drawNumMirror(0, false);
        }
    }

    private void transport(Enum.State anim, int zoneNum) {
        if (this._frame <= 0 * this._interval) {
            this.resetScreen();
            this._frame = 0;
            this._character.drawNumMirror(0, false);
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() - this._character.getSizeX() / this.getScale() - 6);
            this._character.setVisible(true);
            this._itemLabel.setVisible(false);
            int d = 0;
            switch (anim) {
                case BirdraTransport: {
                    d = 97;
                    break;
                }
                case GarudaTransport: {
                    d = 234;
                    break;
                }
                case PhoenixTransport: {
                    d = 292;
                }
            }
            EvolutionInfo mon = this._controller.getModel().getDigimon().getEvolution().getDigimon(d);
            this.setOppSprites(this.getOppSet(mon.getNewStage(), mon.getNewSpriteSet(), mon.getNewSpriteNum()));
            this._opponent.setSize(48, 48);
            this._opponent.setLoc(this._character.getLocX() / this.getScale() - this._opponent.getSizeX() / this.getScale(), -this._opponent.getSizeY() / this.getScale());
            this._opponent.setVisible(false);
            this.setItemSet();
            this._itemLabel.drawNumMirror(0, false);
            this._itemLabel.setLocX(this._character.getLocX() / this.getScale() - 36);
            this._itemLabel.setLocY(-6);
        } else if (this._frame == this._interval * 7) {
            this._sounds.playSound(SoundConfig._transportUseTicket);
            this._character.drawNumMirror(5, false);
            this._itemLabel.setVisible(true);
        } else if (this._frame == this._interval * 14) {
            this._character.drawNumMirror(0, false);
            this._itemLabel.setVisible(false);
            this._opponent.setVisible(true);
        } else if (this._frame >= 15 * this._interval && this._frame <= 24 * this._interval) {
            this._opponent.moveDown(1);
        } else if (this._frame > 30 * this._interval && this._frame < 279) {
            if (this._frame == 31 * this._interval) {
                this._sounds.playSound(SoundConfig._transportLiftOff);
            }
            this._opponent.moveLeft(1);
            this._opponent.moveUp(1);
            this._character.moveLeft(1);
            if (this._character.getLocX() / this.getScale() % 6 == 0) {
                this._character.moveUp(1);
            }
        } else if (this._character.getLocX() / this.getScale() <= -this._character.getSizeX() / this.getScale() && this._animValue3 != 1) {
            this.fade(279);
            if (this._animValue >= 255 && this._animValue2 == 255) {
                PhysicalState digimon = this._controller.getModel().getDigimon();
                digimon.transport(anim, zoneNum);
                this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
            } else if (this._animValue >= 255 && this._animValue2 == 0) {
                this.setSpriteCharDefault();
                this._character.setLocY(-this._character.getSizeY() / this.getScale());
                this._animValue3 = 1;
                this._character.drawNumMirror(9, false);
            }
        } else if (this._animValue3 == 1 && this._frame < 70 * this._interval && this._character.getLocY() / this.getScale() < this._mainDisplay.getHeight() / this.getScale() - this._character.getSizeY() / this.getScale() - 3) {
            this._character.moveDown(2);
            if (this._character.getLocY() > this._mainDisplay.getHeight() / this.getScale() - this._character.getSizeY() / this.getScale() - 3) {
                this._character.setLocY(this._mainDisplay.getHeight() / this.getScale() - this._character.getSizeY() / this.getScale() - 3);
            }
        } else if (this._frame == 416) {
            this._character.drawNumMirror(10, false);
            this._sounds.playSound(SoundConfig._flyTransportFall);
        } else if (this._frame == 70 * this._interval) {
            this._character.drawNumMirror(9, false);
            this._character.moveUp(1);
            this._character.moveRight(1);
        } else if (this._frame == 71 * this._interval) {
            this._character.moveRight(1);
        } else if (this._frame == 72 * this._interval) {
            this._sounds.playSound(SoundConfig._flyTransportFall);
            this._character.drawNumMirror(10, false);
            this._character.moveDown(1);
            this._character.moveRight(1);
        } else if (this._frame == 73 * this._interval) {
            this._character.drawNumMirror(9, false);
            this._character.moveUp(1);
            this._character.moveRight(1);
        } else if (this._frame == 74 * this._interval) {
            this._character.moveRight(1);
        } else if (this._frame == 75 * this._interval) {
            this._sounds.playSound(SoundConfig._flyTransportFall);
            this._character.drawNumMirror(10, false);
            this._character.moveDown(1);
            this._character.moveRight(1);
        } else if (this._frame == 81 * this._interval) {
            this._character.drawNumMirror(0, false);
        } else if (this._frame == 87 * this._interval) {
            this._character.drawNumMirror(6, false);
        } else if (this._frame == 93 * this._interval) {
            this.endAnim();
        }
        if (this._frame % (this._interval * 5) == 0) {
            if (this._opponent.getSpriteNum() == 0) {
                this._opponent.drawNumMirror(1, false);
            } else {
                this._opponent.drawNumMirror(0, false);
            }
        }
        if (this._frame % (this._interval * 7) == 0) {
            if (this._character.getSpriteNum() == 0) {
                this._character.drawNumMirror(1, false);
            } else if (this._character.getSpriteNum() == 1) {
                this._character.drawNumMirror(0, false);
            }
        }
    }

    private void fade(int frame) {
        if (this._frame <= frame) {
            this._animRect.changeColor(0, 0, 0, 0);
            this._animRect.setVisible(true);
            this._animValue = 0;
            this._animValue2 = 255;
        } else if (this._animValue < 255 && this._animValue2 >= 255) {
            this._animValue += 5;
            if (this._animValue > 255) {
                this._animValue = 255;
            }
            this._animRect.changeColor(0, 0, 0, this._animValue);
        } else if (this._animValue2 >= 0 && this._animValue >= 255) {
            this._animValue2 -= 5;
            if (this._animValue2 < 0) {
                this._animValue2 = 0;
            }
            this._animRect.changeColor(0, 0, 0, this._animValue2);
        }
    }

    private void changeLife(int life) {
        if (this._frame <= 0 * this._interval) {
            this.resetScreen();
            this._frame = 0;
            this.drawLife(life);
        } else if (this._frame == 10 * this._interval) {
            boolean dec = life < this._controller.getModel().getDigimon().getWorld().getAdventureLife();
            this._sounds.playSound(dec ? SoundConfig._adventureLifeDecrease : SoundConfig._adventureLifeIncrease);
            this.drawLife(this._controller.getModel().getDigimon().getWorld().getAdventureLife());
        } else if (this._frame == 20 * this._interval) {
            this._fullExercise.setVisible(false);
            this._exerciseLabel.setVisible(false);
            this._exerciseLabel.setSize(46, 14);
            this._exerciseLabel.setLocX(81 - this._xPad);
            this._exerciseLabel.setLocY(97 - this._yPad);
            this._fullExercise.setSize(46, 14);
            this._fullExercise.setLocX(81 - this._xPad);
            this._fullExercise.setLocY(97 - this._yPad);
            this.endAnim();
            if (life < this._controller.getModel().getDigimon().getWorld().getAdventureLife()) {
                this._controller.getModel().getDigimon().setCurrentState(Enum.State.Cheering);
            }
        }
    }

    private void investigateLeft(Enum.State anim) {
        int firstGoal = -this._meatButton.getSizeX() - this._character.getSizeX() / 2 + this._meatButton.getSizeX() + 4 * this.getScale();
        if (this._frame <= 0) {
            this._frame = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.setVisible(true);
        } else if (this._frame % (this._interval * 2) == 0 && this._character.getLocX() > firstGoal) {
            int currentNum = this._character.getSpriteNum();
            int spriteNum = this.getSpriteNum();
            int num = 0;
            num = currentNum == spriteNum + 1 ? spriteNum : spriteNum + 1;
            if (this._character.getLocX() > firstGoal) {
                this._character.moveLeft(3);
                this._character.drawNumMirror(num, false);
                this._frame = 0;
            }
        } else if (this._character.getLocX() <= firstGoal) {
            if (this._frame < this._interval * 20) {
                if (this._frame == this._interval * 5) {
                    this._emotionLabel.setLocX(this._character.getLocX() / this.getScale() + this._character.getSizeX() / this.getScale() + 3);
                    this._emotionLabel.removeIcon();
                    this._emotionLabel.setText(this.scaleTextPadding("."));
                    this._emotionLabel.setVisible(true);
                } else if (this._frame == this._interval * 10) {
                    this._emotionLabel.setText(this.scaleTextPadding(".."));
                } else if (this._frame == this._interval * 15) {
                    this._emotionLabel.setText(this.scaleTextPadding("..."));
                }
            }
            if (this._frame == this._interval * 20) {
                this._emotionLabel.setText(this.scaleTextPadding(""));
                this._emotionLabel.setAltIcon("attention");
                if (anim == Enum.State.DiscoverEnemy) {
                    this._sounds.playSound(SoundConfig._discoverEnemy);
                    this._character.drawNumMirror(6, false);
                } else {
                    this._sounds.playSound(SoundConfig._discoverConsumable);
                    this._character.drawNumMirror(5, false);
                }
            } else if (this._frame == this._interval * 25) {
                this._emotionLabel.setVisible(false);
                this._emotionLabel.setLocX(103 - this._xPad);
                this.endAnim();
                if (anim == Enum.State.DiscoverEnemy) {
                    this._controller.onDiscoverEnemy();
                } else {
                    this._controller.onDiscoverItem();
                }
            }
        }
    }

    private void returnItem() {
        int secondGoal = this._mainDisplay.getWidth() / 2 - (this._character.getSizeX() + 4 * this.getScale()) / 4;
        if (this._frame <= 0) {
            this._frame = 0;
            this.resetScreen();
            this._character.setVisible(true);
            PhysicalState digimon = this._controller.getModel().getDigimon();
            int[] gift = digimon.getGift();
            if (gift[1] == 0) {
                for (Item i : digimon.getItems()) {
                    if (i.getID() != gift[0]) continue;
                    this._itemType = i;
                    this.setItemSet();
                    this._meatButton.setIcon(this._itemLabel.getSpriteSheet()[0]);
                    break;
                }
            } else if (gift[1] == 1) {
                for (FoodType f : digimon.getFoodTypes()) {
                    if (f.getID() != gift[0]) continue;
                    this._foodType = f;
                    this.setFoodSet();
                    this._meatButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
                    break;
                }
            }
            this._meatButton.setLocY(this._mainDisplay.getHeight() / this.getScale() / 2 - this._meatButton.getSizeY() / this.getScale() / 2);
            this._meatButton.setLocX(-this._meatButton.getSizeX() / this.getScale() - this._character.getSizeX() / this.getScale() / 2);
        } else if (this._frame % (this._interval * 2) == 0) {
            int currentNum = this._character.getSpriteNum();
            int spriteNum = this.getSpriteNum();
            int num = 0;
            num = currentNum == spriteNum + 1 ? spriteNum : spriteNum + 1;
            if (this._character.getLocX() < secondGoal) {
                this._character.moveRight(3);
                this._meatButton.moveRight(3);
                this._character.drawNumMirror(num, true);
            } else if (this._frame >= this._interval * 52) {
                this._emotionLabel.removeIcon();
                this._controller.giftEnd();
            } else {
                this._character.drawNumMirror(5, false);
                this._meatButton.setVisible(true);
            }
        }
    }

    private void gifting() {
        int firstGoal = -this._meatButton.getSizeX() - this._character.getSizeX() / 2 + this._meatButton.getSizeX() + 4 * this.getScale();
        int secondGoal = this._mainDisplay.getWidth() / 2 - (this._character.getSizeX() + 4 * this.getScale()) / 4;
        if (this._frame <= 0) {
            this._frame = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.setVisible(true);
            PhysicalState digimon = this._controller.getModel().getDigimon();
            int[] gift = digimon.getGift();
            if (gift[1] == 0) {
                for (Item i : digimon.getItems()) {
                    if (i.getID() != gift[0]) continue;
                    this._itemType = i;
                    this.setItemSet();
                    this._meatButton.setIcon(this._itemLabel.getSpriteSheet()[0]);
                    this._meatButton.setName(i.getID() + "");
                    break;
                }
            } else if (gift[1] == 1) {
                for (FoodType f : digimon.getFoodTypes()) {
                    if (f.getID() != gift[0]) continue;
                    this._foodType = f;
                    this.setFoodSet();
                    this._meatButton.setIcon(this._foodLabel.getSpriteSheet()[0]);
                    this._meatButton.setName(f.getID() + "");
                    break;
                }
            }
            this._meatButton.setSize(24, 24);
            this._meatButton.setLocY(this._mainDisplay.getHeight() / this.getScale() / 2 - this._meatButton.getSizeY() / this.getScale() / 2);
            this._meatButton.setLocX(-this._meatButton.getSizeX() / this.getScale() - this._character.getSizeX() / this.getScale() / 2);
        } else if (this._frame % (this._interval * 2) == 0) {
            int currentNum = this._character.getSpriteNum();
            int spriteNum = this.getSpriteNum();
            int num = 0;
            num = currentNum == spriteNum + 1 ? spriteNum : spriteNum + 1;
            if (this._character.getLocX() > firstGoal && this._meatButton.getLocX() == firstGoal - this._meatButton.getSizeX() - 4 * this.getScale()) {
                this._character.moveLeft(3);
                this._character.drawNumMirror(num, false);
            } else if (this._character.getLocX() < secondGoal) {
                this._character.moveRight(3);
                this._meatButton.moveRight(3);
                this._character.drawNumMirror(num, true);
            } else if (this._frame % (this._interval * 45) == 0) {
                this._emotionLabel.removeIcon();
                this._controller.giftEnd();
            }
            if (this._character.getLocX() >= secondGoal) {
                this._character.drawNumMirror(5, false);
                this._meatButton.setVisible(true);
            }
        }
    }

    private void attention(int num1, int num2) {
        if (this._frame % (this._interval * 6) == 0) {
            if (this._emotionLabel.getIcon() == null) {
                this._sounds.playSound(SoundConfig._attention);
                this._emotionLabel.setAltIcon("attention");
                this._character.drawNumMirror(this.getSpriteNum() + num1, true);
            } else {
                this._emotionLabel.removeIcon();
                this._character.drawNumMirror(this.getSpriteNum() + num2, true);
            }
        }
        if (this._frame <= 0) {
            this._controller.slowClock();
            this._frame = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            this._character.setVisible(true);
            this._keyboard.setCursorPosition(0);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._character});
        } else if (this._frame >= Config._endAttentionAlert * this._interval) {
            this._controller.attentionFail(this._currentAnim);
            this.endAnim();
        }
        this._emotionLabel.setVisible(true);
    }

    private void drawLife(int life) {
        int newSize = 32 * life;
        this._exerciseLabel.setSize(92, 28);
        this._exerciseLabel.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - this._exerciseLabel.getSizeX() / this.getScale() / 2, this._mainDisplay.getHeight() / this.getScale() / 2 - this._exerciseLabel.getSizeY() / this.getScale() / 2 + 1);
        this._exerciseLabel.setIcon(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "emptyHearts.png", (double)this.getScale() * 2.0));
        this._fullExercise.setLoc(this._exerciseLabel.getLocX() / this.getScale(), this._exerciseLabel.getLocY() / this.getScale());
        this._fullExercise.setSize(newSize, 28);
        this._fullExercise.setIcon(ViewUtil.resizeImage(this.MOD_FOLDER, this.RESOURCES_FOLDER, "fullHearts.png", (double)this.getScale() * 2.0));
        this._exerciseLabel.setVisible(true);
        this._fullExercise.setVisible(true);
    }

    private void refuse() {
        int sprite;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.checkFilth(digimon);
        this.stateNumTic(digimon, false);
        int n = sprite = digimon.getCurrentMood() == Enum.Mood.Depressed ? 9 : 4;
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this._battleFlash.setVisible(false);
            this._sounds.playSound(SoundConfig._refuse);
            this._character.setVisible(true);
            this.setSpriteCharDefault();
            this.adjustCharacterForFilth();
            this._character.drawNumMirror(sprite, true);
        }
        if (this._frame == this._interval * 6) {
            this._character.drawNumMirror(sprite, false);
            this._sounds.playSound(SoundConfig._refuse);
        }
        if (this._frame == this._interval * 12) {
            this._character.drawNumMirror(sprite, true);
            this._sounds.playSound(SoundConfig._refuse);
        }
        if (this._frame == this._interval * 18) {
            this._character.drawNumMirror(sprite, false);
            this._sounds.playSound(SoundConfig._refuse);
        }
        if (this._frame == this._interval * 24) {
            this.endAnim();
        }
    }

    private void xAntibodyInc() {
        this._itemType = this._controller.getModel().getDigimon().getItemByID(14);
        this._frame = -1;
        this._currentAnim = Enum.State.X_Program;
        this.xProgram();
    }

    private void xProgram() {
        int start = 4;
        int goal = 62 - this._yPad;
        int loc = 81 - this._xPad;
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._roomEffect.setVisible(false);
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(loc);
            this._itemLabel.setLoc(3, -this._itemLabel.getSizeY() / this.getScale());
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
            this._sounds.loopSound(SoundConfig._xProgramDescendLoop, 3);
        } else if (this._itemLabel.getLocY() / this.getScale() < goal) {
            this._itemLabel.moveDown(1);
        }
        if (this._frame == this._interval * start) {
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * start * 2) {
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * start * 3) {
            this._itemLabel.drawNumMirror(4, false);
            this._sounds.playSound(SoundConfig._xProgramShrink);
        } else if (this._frame == this._interval * start * 4) {
            this._itemLabel.drawNumMirror(5, false);
        } else if (this._frame == this._interval * start * 5) {
            this._itemLabel.drawNumMirror(6, false);
            this._sounds.playSound(SoundConfig._xProgramShrink);
        } else if (this._frame == this._interval * start * 6) {
            this._itemLabel.drawNumMirror(7, false);
        } else if (this._frame == this._interval * start * 7) {
            this._character.drawNumMirror(10, false);
            this._itemLabel.drawNumMirror(8, false);
            this._sounds.playSound(SoundConfig._xProgramShrink);
        } else if (this._frame == this._interval * start * 8) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 1) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 2) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 3) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 4) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 5) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 6) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * start * 8 + 7) {
            this._itemLabel.moveRight(2);
        } else if (this._frame == 210) {
            this._itemLabel.moveRight(3);
            this._sounds.playSound(SoundConfig._xProgramHit);
        } else if (this._frame == 215) {
            this._roomEffect.setAltIcon("lightsOff");
            this._roomEffect.setVisible(true);
            this._itemLabel.setVisible(false);
            this._character.moveRight(1);
            this._character.moveUp(1);
        } else if (this._frame == 230) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 41) {
            this._roomEffect.setVisible(true);
            this._character.moveUp(1);
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 43) {
            this._roomEffect.setVisible(false);
            this._character.moveRight(1);
        } else if (this._frame == this._interval * 44) {
            this._character.moveRight(1);
            this._character.moveDown(1);
        } else if (this._frame == this._interval * 45) {
            this._character.moveRight(1);
            this._character.moveDown(1);
        } else if (this._frame == this._interval * 46) {
            this._character.moveRight(1);
            this._character.moveUp(1);
        } else if (this._frame == this._interval * 47) {
            this._character.moveRight(1);
            this._character.moveDown(1);
        } else if (this._frame == this._interval * 48) {
            this._character.moveRight(1);
            this._character.moveUp(1);
        } else if (this._frame == this._interval * 49) {
            this._character.moveRight(1);
            this._character.moveDown(1);
        } else if (this._frame == this._interval * 60) {
            this.endAnim();
        }
        if (this._frame < this._interval * 50 && this._frame >= this._interval * start * 7 && this._frame % (8 * this._interval) == 0) {
            this.shakeObj(this._character, loc);
        } else if (this._frame < this._interval * start * 7 && this._frame % (8 * this._interval) == 0) {
            if (this._character.getSpriteNum() == 1) {
                this._character.drawNumMirror(6, false);
            } else if (this._character.getSpriteNum() == 6) {
                this._character.drawNumMirror(1, false);
            }
        }
    }

    private void dnaCharge() {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this.setSpriteCharDefault();
            this._roomEffect.setVisible(false);
            this._character.drawNumMirror(this.getSpriteNum(), false);
            this._character.setLocX(3 + this._character.getLocX() / this.getScale());
            this._roomEffect.setAltIcon("dnaWash");
            this._roomEffect.setSize(105, 120);
            this._roomEffect.setLocY(-1 - this._roomEffect.getSizeY() / this.getScale());
            this._roomEffect.setLocX(-1);
            this._fieldLabel.setLoc(-4 - this._fieldLabel.getSizeX() / this.getScale() + this._character.getLocX() / this.getScale(), 1 - this._fieldLabel.getSizeY() / this.getScale());
            this.checkField(Enum.Field.values()[this._consumablePage]);
            this._fieldLabel.setVisible(true);
            this._character.setVisible(true);
            this._frame = 0;
        } else if (this._frame == this._interval * 1) {
            this._sounds.playSound(SoundConfig._dnaDrop);
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 2) {
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 3) {
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 4) {
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 5) {
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 6) {
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 7) {
            this._fieldLabel.moveDown(6);
        } else if (this._frame == this._interval * 9) {
            this._fieldLabel.moveLeft(1);
        } else if (this._frame == this._interval * 11) {
            this._fieldLabel.moveRight(2);
        } else if (this._frame == this._interval * 13) {
            this._fieldLabel.moveLeft(1);
        } else if (this._frame == this._interval * 16) {
            this._sounds.playSound(SoundConfig._dnaChargeInsert);
            this._fieldLabel.moveDown(2);
        } else if (this._frame == this._interval * 21) {
            this._sounds.playSound(SoundConfig._dnaWash);
            this._roomEffect.setVisible(true);
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 22) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 23) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 24) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 25) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 26) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 27) {
            this._sounds.playSound(SoundConfig._dnaWashCollide);
            this._character.drawNumMirror(9, false);
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 28) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 29) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 30) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 31) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 32) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 33) {
            this._roomEffect.moveDown(9);
        } else if (this._frame == this._interval * 34) {
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 35) {
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 36) {
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 37) {
            this._fieldLabel.moveDown(3);
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 38) {
            this._fieldLabel.moveDown(3);
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 39) {
            this._fieldLabel.moveDown(3);
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 40) {
            this._fieldLabel.moveDown(3);
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 41) {
            this._fieldLabel.moveDown(3);
            this._roomEffect.moveDown(8);
        } else if (this._frame == this._interval * 43) {
            this._roomEffect.setSize(105, 60);
            this._roomEffect.setLocX(26 - this._xPad);
            this._roomEffect.setLocY(0);
            this._roomEffect.setVisible(false);
            this.setSpriteCharDefault();
            this.endAnim();
        }
        if (this._frame % 30 * this._interval == 0) {
            if (this._character.getSpriteNum() == 1) {
                this._character.drawNumMirror(0, false);
            } else if (this._character.getSpriteNum() == 0) {
                this._character.drawNumMirror(1, false);
            }
        }
    }

    private void setAssistantSprites() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        EvolutionInfo e = digimon.getEvolution().getDigimon(digimon.getAssistantID());
        this.setOppSprites(this.getOppSet(e.getNewStage(), e.getNewSpriteSet(), e.getNewSpriteNum()));
        this._opponent.setSize(48, 48);
        this._opponent.setLocY(-this._opponent.getHeight() / this.getScale());
    }

    private void assistantClean() {
        this.stateAnims(this._controller.getModel().getDigimon(), false);
        if (this._frame <= 0) {
            this._frame = 0;
            this.setAssistantSprites();
            this._opponent.setLocX(6);
            this._opponent.drawNum(0);
            this._opponent.setIcon(ViewUtil.flipVertically(this._opponent.getIcon()));
            this.adjustCharacterForFilth();
        } else if (this._frame < 16 * this._interval && this._frame % this._interval == 0) {
            this._opponent.moveDown(3);
            this._filthLabel.moveRight(4);
            this.adjustCharacterForFilth();
        } else if (this._frame == 16 * this._interval) {
            this._opponent.moveLeft(6);
        } else if (this._frame == 17 * this._interval) {
            this._opponent.moveRight(6);
        } else if (this._frame == 18 * this._interval) {
            this._opponent.moveUp(24);
        } else if (this._frame == 19 * this._interval) {
            this._opponent.moveUp(24);
        } else if (this._frame == 20 * this._interval) {
            this._controller.getModel().getDigimon().processAutoCarePrice();
            this.endAnim();
            this._controller.onClean();
        }
    }

    private void assistantLights(PhysicalState digimon) {
        if (this._frame <= 0) {
            this._frame = 0;
            this.setAssistantSprites();
            this._opponent.setLocX(6);
            this._opponent.drawNum(0);
            this._opponent.setIcon(ViewUtil.flipVertically(this._opponent.getIcon()));
        } else if (this._frame < 15 * this._interval && this._frame % this._interval == 0) {
            this._opponent.moveDown(3);
            this._character.moveRight(2);
            this.adjustEmotionLabel();
        } else if (this._frame == 16 * this._interval) {
            this._opponent.moveLeft(6);
        } else if (this._frame == 19 * this._interval) {
            this._opponent.moveRight(6);
        } else if (this._frame == 20 * this._interval) {
            this._controller.onLights();
            digimon.processAutoCarePrice();
            this.endAnim();
        }
        this.idleSleep(digimon);
    }

    private void assistantFeed() {
        if (this._frame <= 0) {
            this.setAssistantSprites();
        } else if (this._frame == 1 * this._interval) {
            this._opponent.setLocX(this._foodLabel.getLocX() / this.getScale() - this._foodLabel.getWidth() / this.getScale() / 2 - 12);
            this._opponent.setLocY(this._foodLabel.getLocY() / this.getScale() - this._opponent.getHeight() / this.getScale());
            this._opponent.drawNumMirror(1, true);
            this._opponent.setVisible(true);
        } else if (this._frame == this._interval * 2) {
            this._opponent.moveDown(11);
        } else if (this._frame == this._interval * 4) {
            this._opponent.moveDown(11);
        } else if (this._frame == this._interval * 6) {
            this._opponent.moveDown(11);
        } else if (this._frame == this._interval * 8) {
            this._opponent.drawNumMirror(1, false);
            this._opponent.moveLeft(24);
        } else if (this._frame == this._interval * 10) {
            this._opponent.moveLeft(24);
        } else if (this._frame > this._interval * 10) {
            this._opponent.setVisible(false);
        }
        this.eat(Enum.State.Assistant_Feed);
    }

    private void eat(Enum.State s) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.checkFilth(digimon);
        this.stateNumTic(digimon, false);
        double mod = digimon.getHunger() == 0 || digimon.getGlutton() > 0 ? 0.9 : (digimon.getGlutton() < 0 ? 1.1 : 1.0);
        int pad = this._filthLabel.getSizeX() / this.getScale();
        if (this._frame <= this._interval * 0) {
            this._feedButton.setIsEnabled(s != Enum.State.Assistant_Feed);
            this._frame = 0;
            this._foodLabel.setSize(24, 24);
            this.resetScreen();
            this._menuButton.setVisible(true);
            this._keyboard.setCursorPosition(0);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
            this.setFoodSet();
            this._foodLabel.setVisible(true);
            this._foodLabel.setLocX(31 - this._xPad + pad);
            this._foodLabel.setLocY(54 - this._yPad);
            this._foodLabel.drawNumMirror(0, false);
            this._character.drawNumMirror(this.getSpriteNum(), false);
            this._character.setVisible(true);
            this._character.setLocX(55 - this._xPad + pad);
        } else if (this._frame == this._interval * 2) {
            this._foodLabel.setLocY(65 - this._yPad);
        } else if (this._frame == this._interval * 4) {
            this._foodLabel.setLocY(76 - this._yPad);
        } else if (this._frame == this._interval * 6) {
            this._foodLabel.setLocY(87 - this._yPad);
        } else if (this._frame == this._interval * (int)Math.pow(10.0, mod)) {
            this._character.drawNumMirror(this.getSpriteNum() + 8, false);
        } else if (this._frame == this._interval * (int)Math.pow(14.0, mod)) {
            this._sounds.playSound(SoundConfig._eat);
            this._character.drawNumMirror(this.getSpriteNum() + (this._foodType.getSpriteNum() == 20 || digimon.getHunger() >= digimon.getOvereatLimit() || this._foodType.getType().contains((Object)digimon.getDislikedFood()) ? 9 : 7), false);
            this._foodLabel.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (int)Math.pow(18.0, mod)) {
            this._character.drawNumMirror(this.getSpriteNum() + 8, false);
            if (s == Enum.State.Munching) {
                this._frame = 0;
                this._currentAnim = Enum.State.DisposeFood;
                this.disposeFood();
            } else if (this._controller.getModel().getDigimon().getBaseWeight() >= 40) {
                this._frame = (int)((double)this._interval * Math.pow(26.0, mod));
            }
        } else if (this._frame == this._interval * (int)Math.pow(22.0, mod)) {
            this._sounds.playSound(SoundConfig._eat);
            this._character.drawNumMirror(this.getSpriteNum() + (this._foodType.getSpriteNum() == 20 || digimon.getHunger() >= digimon.getOvereatLimit() || this._foodType.getType().contains((Object)digimon.getDislikedFood()) ? 9 : 7), false);
            this._foodLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * (int)Math.pow(26.0, mod)) {
            this._character.drawNumMirror(this.getSpriteNum() + 8, false);
        } else if (this._frame == this._interval * (int)Math.pow(30.0, mod)) {
            this._sounds.playSound(SoundConfig._lastBite);
            this._character.drawNumMirror(this.getSpriteNum() + (this._foodType.getSpriteNum() == 20 || digimon.getHunger() >= digimon.getOvereatLimit() || this._foodType.getType().contains((Object)digimon.getDislikedFood()) ? 9 : 7), false);
            this._foodLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * (int)Math.pow(34.0, mod)) {
            this._foodLabel.setVisible(false);
            this._foodLabel.setLocX(-100);
            this._menuButton.setVisible(false);
            if (s == Enum.State.Assistant_Feed) {
                digimon.processAutoCarePrice();
            }
            this.endAnim();
        }
    }

    private void disposeFood() {
        if (this._frame <= 0) {
            this._character.drawNum(1);
        } else if (this._frame == 5 * this._interval) {
            this._character.drawNumMirror(1, true);
        } else if (this._frame > 10 * this._interval && this._foodLabel.getLocY() < this._mainDisplay.getHeight()) {
            this._foodLabel.moveDown(1);
        } else if (this._foodLabel.getLocY() >= this._mainDisplay.getHeight()) {
            this.endAnim();
        }
    }

    private void bandage() {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this._menuButton.setVisible(true);
            this._frame = 0;
            this.setItemSet();
            this._itemLabel.setVisible(true);
            this._itemLabel.setLocX(31 - this._xPad);
            this._itemLabel.setLocY(53 - this._yPad);
            this._itemLabel.drawNumMirror(0, false);
            this._character.drawNumMirror(this.getSpriteNum() + 9, false);
            this._character.setVisible(true);
            this._character.setLocX(55 - this._xPad);
        }
        if (this._frame == this._interval * 4) {
            this._itemLabel.setLocY(64 - this._yPad);
        }
        if (this._frame == this._interval * 8) {
            this._sounds.playSound(SoundConfig._useBandage);
            this._itemLabel.drawNumMirror(1, false);
        }
        if (this._frame == this._interval * 13) {
            this._sounds.playSound(SoundConfig._useBandage);
            this._itemLabel.drawNumMirror(2, false);
        }
        if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._lastBandage);
            this._itemLabel.drawNumMirror(3, false);
        }
        if (this._frame == this._interval * 23) {
            this._itemLabel.setVisible(false);
            this._itemLabel.setLocX(-100);
            this._frame = 0;
            this._currentAnim = Enum.State.Cheering;
            this.cheer(true, SoundConfig._happy, true);
        }
    }

    private void deading() {
        if (this._frame <= 0 * this._interval) {
            this._sounds.loopSound(SoundConfig._dieLoop, 2);
            this._frame = 0;
            this.resetScreen();
            this._character.setVisible(false);
            this.setDeathIcon();
        } else if (this._frame >= 20 * this._interval) {
            this.endAnim();
            this._controller.onDie(true);
        }
    }

    private void dying() {
        if (this._frame <= 0) {
            this._controller.slowClock();
            this.resetScreen();
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._character});
            this._keyboard.setCursorPosition(0);
            this.setSpriteCharDefault();
            this._character.setVisible(true);
            this._character.drawNumMirror(10, true);
            this._sounds.playSound(SoundConfig._dying, SoundConfig._musicVolume);
            this._emotionLabel.setVisible(true);
            this._emotionLabel.setAltIcon("dying");
            this._animValue = (int)this._sounds.getClipLength(SoundConfig._dying) * this._interval * 10;
            this._frame = 0;
        } else if (this._frame >= this._animValue) {
            if (this._controller.getNumHits() > Config._hitsToSave * (this._controller.getModel().getDigimon().getSavedFromDeath() + 1)) {
                this._controller.onDie(false);
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.resetScreen();
                this._frame = 0;
                this._currentAnim = Enum.State.Dead;
                this.deading();
            }
        } else if (this._frame % (10 * this._interval) == 0) {
            if (!this._emotionLabel.getIcon().equals(this._emotionLabel.getAltSprite("dying2"))) {
                this._emotionLabel.setAltIcon("dying2");
                this._character.moveLeft(1);
            } else {
                this._emotionLabel.setAltIcon("dying");
                this._character.moveRight(1);
            }
        }
    }

    private void setFrozenIcon() {
        this._character.setIcon(this._frozen);
        this._character.setVisible(true);
    }

    private void setDeathIcon() {
        this._character.setAltIcon("death");
        this._character.setVisible(true);
    }

    private void clean() {
        boolean able;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        boolean bl = able = digimon.getAlive() && !digimon.isPaused() && digimon.getGrowthStage() != Enum.Stage.Egg;
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this._sounds.playSound(SoundConfig._wash);
            this._character.setVisible(true);
            this.adjustCharacterForFilth();
            if (able) {
                this._character.drawNum(0);
            }
            this._filthLabel.setVisible(true);
            this._washLabel.setLocX(6 + this._character.getLocX() / this.getScale() + this._character.getSizeX() / this.getScale());
            if (this._washLabel.getLocX() < 6 * this.getScale() + this._mainDisplay.getWidth()) {
                this._washLabel.setLocX(6 + this._mainDisplay.getWidth() / this.getScale());
            }
            this._washLabel.setVisible(true);
        } else if (this._frame > 1 * this._interval && this._washLabel.getLocX() > -this._washLabel.getWidth()) {
            this._washLabel.moveLeft(3);
            if (this._washLabel.getLocX() <= this._character.getLocX() + this._character.getWidth() + 1) {
                this._character.moveLeft(3);
                this._filthLabel.moveLeft(3);
                if (able && this._character.getSpriteNum() != 4) {
                    this._character.drawNum(4);
                }
            }
        } else if (this._frame > this._interval * 1) {
            boolean filth = digimon.isFilth();
            this._controller.onCleanFinish();
            this._washLabel.setVisible(false);
            this._washLabel.setLocX(-100);
            this.resetFilth();
            if (able && filth) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.setSpriteCharDefault();
                this.endAnim();
            }
        }
    }

    private void resetFilth() {
        this._filthLabel.setLocX(0);
        this._filthLabel.setSizeX(0);
        this._filthLabel.getAltSprites().clear();
    }

    private void battlePrep() {
        if (this._controller.getBattle() != null) {
            this._roomEffect.removeIcon();
            this._emotionLabel.removeIcon();
            this._healthBar.setLocX(26 - this._xPad);
            this._healthBarFull.setLocX(26 - this._xPad);
            this._healthBarFull.setVisible(false);
            this._healthBar.setVisible(false);
            this._character.setVisible(false);
            this._character.setLocX(105 - this._character.getSizeX() / this.getScale() + this._healthBar.getSizeX() / this.getScale() + 6 - this._xPad);
            this._attackSprite.setSizeX(24);
            this._attackSprite.setSizeY(24);
            this._attackSprite.setLocX(75 - this._xPad);
            this._attackSprite.setLocY(this._character.getLocY() / this.getScale());
            Enemy enemy = this._controller.getBattle().getEnemy();
            this.setOppSprites(enemy);
            this._opponent.setSizeX(48);
            this._opponent.setSizeY(48);
            this.setupBattleOpponent();
        }
    }

    private void setBattleBags() {
        this._opponent.setSpriteSheet(this._battleBags.getSpriteSheet());
        this._opponent.setSpriteSheetMirror(null);
        this._opponent.setSpriteLoc(this._battleBags.getSpriteLoc());
        this._opponent.setSizeX(40);
        this._opponent.setSizeY(52);
    }

    private int getBattleBagSprite(Enum.Attribute a) {
        switch (a) {
            case Data: {
                return 4;
            }
            case Virus: {
                return 2;
            }
        }
        return 0;
    }

    private void setHealthBarSize(boolean isPlayer) {
        int oriHealth = 0;
        int maxHealth = 0;
        if (isPlayer) {
            oriHealth = this._controller.getBattle().getHealth();
            maxHealth = this._controller.getBattle().getFullHealth();
        } else {
            oriHealth = this._controller.getBattle().getEnemyHealth();
            maxHealth = this._controller.getBattle().getEnemy().getEnemyHealth();
        }
        this.checkHealth(oriHealth, maxHealth);
    }

    private void checkHealth(int oriHealth, int maxHealth) {
        int fullSize = 60;
        double percentHealth = (double)(oriHealth < 0 ? 0 : oriHealth) / (double)maxHealth;
        int newSize = fullSize - (int)((double)fullSize * percentHealth);
        this._healthBar.setSizeY(newSize < 0 ? 0 : newSize);
    }

    private void jogressFlash() {
        boolean isConnect = this._controller.getConnectJogress() != null;
        this._character.setVisible(false);
        if (this._frame <= 0) {
            this._controller.slowClock();
            if (this._longClip == null) {
                this._longClip = this._sounds.loopSound(SoundConfig._jogressFlash, SoundConfig._masterVolume);
            }
            this._frame = 10 * this._interval;
            this._userInputTitle.setVisible(false);
            this._keyboard.setCursorPosition(0);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._battleFlash});
            this.resetScreen();
            this._battleFlash.setVisible(true);
        }
        if (this._frame == this._interval * 10) {
            this._battleFlash.setAltIcon(isConnect ? "jogressConnectStart" : "jogressStart");
        } else if (this._frame == this._interval * 12) {
            this._battleFlash.setAltIcon(isConnect ? "jogressConnectStartFlash" : "jogressStartFlash");
        } else if (this._frame == this._interval * 14) {
            this._battleFlash.setAltIcon(isConnect ? "jogressConnectStart" : "jogressStart");
        } else if (this._frame == this._interval * 16) {
            this._frame = 8 * this._interval;
            this._battleFlash.setAltIcon(isConnect ? "jogressConnectStartFlash" : "jogressStartFlash");
        }
    }

    private void startJogressAnim() {
        if (this._frame <= this._interval * 0) {
            this.disposeMusic();
            this._frame = 0;
            this._keyboard.clearInteractiveButtons();
            this.resetScreen();
            this._character.setVisible(true);
            this._opponent.setVisible(true);
            this._battleFlash.removeIcon();
            this._battleFlash.setVisible(false);
            this._sounds.playSound(SoundConfig._jogressStart);
            this._opponent.setLocX(26 - this._xPad);
            this._character.setLocX(82 - this._xPad);
            Enemy enemy = this._controller.getJogressPartner();
            SpriteObj opponent = this.getOppSet(enemy.getOppStage(), enemy.getSpriteSet(), enemy.getSpriteNum());
            this._opponent.setSpriteSheet(opponent.getSpriteSheet());
            this._opponent.setSpriteLoc(opponent.getSpriteLoc());
            this._opponent.setSizeX(48);
            this._opponent.setSizeY(48);
            this._opponent.setLocY(this._character.getLocY() / this.getScale());
            this._opponent.drawNumMirror(1, true);
            this._character.drawNumMirror(this.getSpriteNum() + 1, false);
        }
        if (this._frame == this._interval * 8) {
            this._opponent.drawNumMirror(5, true);
            this._character.drawNumMirror(this.getSpriteNum() + 5, false);
        }
        if (this._frame == this._interval * 16) {
            this._opponent.drawNumMirror(1, true);
            this._character.drawNumMirror(this.getSpriteNum() + 1, false);
        }
        if (this._frame == this._interval * 24) {
            this._opponent.drawNumMirror(5, true);
            this._character.drawNumMirror(this.getSpriteNum() + 5, false);
        }
        if (this._frame == this._interval * 32) {
            this._opponent.setVisible(false);
            this.setSpriteCharDefault();
            this.endAnim();
            this._controller.getModel().getDigimon().setCurrentState(Enum.State.Jogress);
        }
    }

    private void battleFlash() {
        boolean isConnect;
        this._character.setVisible(false);
        boolean bl = isConnect = this._controller.getConnectBattle() != null;
        if (this._frame <= 0) {
            this._controller.slowClock();
            if (this._longClip == null) {
                this._longClip = this._sounds.loopSound(SoundConfig._battleFlash, SoundConfig._masterVolume);
            }
            this._userInputTitle.setVisible(false);
            this._frame = this._interval * 10;
            this._keyboard.setCursorPosition(0);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._battleFlash});
            this.resetScreen();
            this._battleFlash.setVisible(true);
        }
        if (this._frame == this._interval * 10) {
            this._battleFlash.setAltIcon(isConnect ? "battleConnectStart" : "battleStart");
        } else if (this._frame == this._interval * 12) {
            this._battleFlash.setAltIcon(isConnect ? "battleConnectStartFlash" : "battleStartFlash");
        } else if (this._frame == this._interval * 14) {
            this._battleFlash.setAltIcon(isConnect ? "battleConnectStart" : "battleStart");
        } else if (this._frame == this._interval * 16) {
            this._battleFlash.setAltIcon(isConnect ? "battleConnectStartFlash" : "battleStartFlash");
        } else if (this._frame == this._interval * 18) {
            this._battleFlash.setAltIcon(isConnect ? "battleConnectStart" : "battleStart");
        } else if (this._frame == this._interval * 20) {
            this._battleFlash.setAltIcon(isConnect ? "battleConnectStartFlash" : "battleStartFlash");
            this._frame = this._interval * 8;
        }
    }

    private void setupBattle() {
        this.disposeMusic();
        this._keyboard.clearInteractiveButtons();
        Battle b = this._controller.getBattle();
        if (b != null && b.getInProgress()) {
            this.battlePrep();
            if (b.getBattleType() == Battle.BattleType.PvP) {
                this._backgroundAnim.checkBackNoAnim(this._controller.getModel().getDigimon(), this._controller.getCurrentMenu(), this.getScale(), b);
            }
        }
        this.resetScreen();
        this._battleFlash.removeIcon();
        this._battleFlash.setVisible(false);
        this._sounds.playSound(SoundConfig._startBattle);
        this.setSpriteCharDefault();
        this.setupOpponent(true, false);
        this._opponent.drawNumMirror(1, true);
        this._opponent.setVisible(true);
        this._frame = 0;
    }

    private void startBattle() {
        if (this._battleFlash.isVisible()) {
            this._battleFlash.setVisible(false);
        }
        if (this._frame <= 0) {
            this.setupBattle();
        } else if (this._frame == this._interval * 8) {
            this._opponent.drawNumMirror(6, true);
        } else if (this._frame == this._interval * 16) {
            this._opponent.drawNumMirror(1, true);
        } else if (this._frame == this._interval * 24) {
            this._opponent.drawNumMirror(6, true);
        } else if (this._frame >= this._interval * 32) {
            this._controller.onStartBattleFinish();
        }
        this._opponent.setVisible(true);
    }

    private void setupOpponent(boolean isAttacker, boolean healthBar) {
        Battle battle = this._controller.getBattle();
        this._healthBar.setLocX(26 - this._xPad);
        this._healthBarFull.setLocX(26 - this._xPad);
        this._healthBar.setVisible(healthBar);
        this._healthBarFull.setVisible(healthBar);
        this._character.setVisible(false);
        if (isAttacker && battle.getOppAttack() != null) {
            Enemy e = battle.getEnemy();
            EvolutionInfo d = this._controller.getModel().getDigimon().getEvolution().getDigimon(e.getIndex());
            switch (battle.getOppAttack()) {
                case Vaccine: {
                    this.checkAttackSprite(Enum.Attribute.Vaccine, e.getOppRed() / (battle.getBattleType() == Battle.BattleType.PvP ? Config._pvpBonusPowerMultiple : 1), true, d.getVaccineNum());
                    break;
                }
                case Data: {
                    this.checkAttackSprite(Enum.Attribute.Data, e.getOppGreen() / (battle.getBattleType() == Battle.BattleType.PvP ? Config._pvpBonusPowerMultiple : 1), true, d.getDataNum());
                    break;
                }
                case Virus: {
                    this.checkAttackSprite(Enum.Attribute.Virus, e.getOppYellow() / (battle.getBattleType() == Battle.BattleType.PvP ? Config._pvpBonusPowerMultiple : 1), true, d.getVirusNum());
                }
            }
            if (battle.getEnemyAttack() >= 2 && battle.getEnemyAttack() >= battle.getAttack()) {
                this.doubleAttack(this._attackSprite);
            } else {
                this._attackSprite.setSizeY(24);
            }
        } else {
            this._opponent.drawNumMirror(4, true);
        }
        this.setupBattleOpponent();
    }

    private void setupBattleOpponent() {
        this._opponent.setLocX(26 - this._xPad + this._healthBar.getSizeX() / this.getScale());
        this._opponent.setLocY(63 - this._yPad);
        this._opponent.setVisible(true);
    }

    private void setupBattleCharacter() {
        this._character.setLocX(105 - this._character.getSizeX() / this.getScale() + this._healthBar.getSizeX() / this.getScale() + 6 - this._xPad);
        this._character.setVisible(true);
    }

    private void setupPlayer(boolean isAttacker) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Battle battle = this._controller.getBattle();
        this._healthBar.setLocX(105 + this._healthBar.getSizeX() / this.getScale() + 5 - this._xPad);
        this._healthBarFull.setLocX(105 + this._healthBar.getSizeX() / this.getScale() + 5 - this._xPad);
        this._healthBar.setVisible(true);
        this._healthBarFull.setVisible(true);
        this._opponent.setVisible(false);
        if (isAttacker) {
            this._character.drawNumMirror(this.getSpriteNum() + 6, false);
            EvolutionInfo d = this._controller.getModel().getDigimon().getEvolution().getDigimon(this._controller.getModel().getDigimon().getIndex());
            switch (battle.getAttackType()) {
                case Vaccine: {
                    this.checkAttackSprite(Enum.Attribute.Vaccine, battle.getRed() / (battle.getBattleType() == Battle.BattleType.PvP ? Config._pvpBonusPowerMultiple : 1), false, d.getVaccineNum());
                    break;
                }
                case Data: {
                    this.checkAttackSprite(Enum.Attribute.Data, battle.getGreen() / (battle.getBattleType() == Battle.BattleType.PvP ? Config._pvpBonusPowerMultiple : 1), false, d.getDataNum());
                    break;
                }
                case Virus: {
                    this.checkAttackSprite(Enum.Attribute.Virus, battle.getYellow() / (battle.getBattleType() == Battle.BattleType.PvP ? Config._pvpBonusPowerMultiple : 1), false, d.getVirusNum());
                }
            }
            if (battle.getAttack() >= 2 && battle.getAttack() >= battle.getEnemyAttack()) {
                this.doubleAttack(this._attackSprite);
            } else {
                this._attackSprite.setSizeY(24);
            }
        } else {
            this._character.drawNumMirror(this.getSpriteNum() + 4, false);
        }
        this.setupBattleCharacter();
    }

    private void waitingTurn() {
        this._opponent.setLocX(27 - this._xPad);
        if (this._frame <= this._interval * 0) {
            this._frame = 7 * this._interval;
            this.resetScreen();
            this.setupPlayer(true);
            this.setupOpponent(true, false);
            this._character.setLocX(81 - this._xPad);
            this._character.setVisible(true);
            this._opponent.setVisible(true);
            this._character.drawNumMirror(this.getSpriteNum(), false);
            this._opponent.drawNumMirror(6, true);
        }
        if (this._frame == this._interval * 14) {
            this._character.drawNumMirror(this.getSpriteNum() + 6, false);
            this._opponent.drawNumMirror(0, true);
            this._opponent.setLocX(27 - this._xPad);
        }
        if (this._frame == this._interval * 21) {
            this._character.drawNumMirror(this.getSpriteNum(), false);
            this._opponent.drawNumMirror(6, true);
            this._opponent.setLocX(27 - this._xPad);
            this._frame = 7 * this._interval;
        }
    }

    private void changeAnim(Enum.State anim) {
        this.endAnim();
        this._currentAnim = anim == null ? Enum.State.None : anim;
        this._controller.getModel().getDigimon().setCurrentState(anim);
    }

    private void battleAttackAnimPlayerSetup(boolean isPlayer, boolean receive) {
        this.resetScreen();
        this._frame = 0;
        this.setHealthBarSize(isPlayer);
        if (isPlayer) {
            this.setupPlayer(!receive);
            if (!receive) {
                this._attackSprite.setLocX(this._character.getLocX() / this.getScale() - this._attackSprite.getSizeX() / this.getScale());
            } else {
                this._attackSprite.setLocX(-this._attackSprite.getSizeX() / this.getScale());
            }
        } else {
            this.setupOpponent(!receive, true);
            if (!receive) {
                this._attackSprite.setLocX(this._opponent.getLocX() / this.getScale() + this._opponent.getSizeX() / this.getScale());
            } else {
                this._attackSprite.setLocX(this._mainDisplay.getWidth() / this.getScale());
            }
        }
    }

    private void battlePlayerShootAnim(boolean isPlayer) {
        boolean isOffScreen = isPlayer && this._attackSprite.getLocX() <= -this._attackSprite.getSizeX() || !isPlayer && this._attackSprite.getLocX() >= this._mainDisplay.getWidth();
        SpriteObj o = isPlayer ? this._character : this._opponent;
        int b = isPlayer ? 1 : -1;
        int interval = 5;
        int shootInterval = 5;
        if (this._frame <= 0) {
            this.battleAttackAnimPlayerSetup(isPlayer, false);
            this._attackSprite.setVisible(false);
            o.drawNumMirror(1, !isPlayer);
        }
        if (this._frame == 3 * interval) {
            o.moveLeft(2 * b);
        } else if (this._frame == 4 * interval) {
            o.drawNumMirror(0, !isPlayer);
            o.moveLeft(2 * b);
        } else if (this._frame == 5 * interval) {
            o.moveLeft(2 * b);
        } else if (this._frame == 6 * interval) {
            o.drawNumMirror(4, !isPlayer);
            o.moveLeft(2 * b);
        } else if (this._frame == 8 * interval) {
            o.moveRight(2 * b);
            o.moveUp(2);
        } else if (this._frame == 9 * interval) {
            o.moveRight(2 * b);
            o.moveUp(2);
        } else if (this._frame == 10 * interval) {
            o.moveRight(1 * b);
            o.moveUp(1);
        } else if (this._frame == 11 * interval) {
            o.moveRight(1 * b);
            o.moveDown(1);
        } else if (this._frame == 12 * interval) {
            o.moveRight(1 * b);
            o.moveDown(2);
        } else if (this._frame == 13 * interval) {
            o.moveRight(2 * b);
            o.moveDown(2);
        } else if (this._frame == 15 * interval) {
            o.moveLeft(3 * b);
        }
        if (this._frame == 16 * interval) {
            o.moveLeft(3 * b);
            o.drawNumMirror(6, !isPlayer);
            if (this._attackSprite.getSizeY() == 48 * this.getScale()) {
                this._sounds.playSound(SoundConfig._strongAttack);
            } else if (this._attackSprite.getSizeY() == 24 * this.getScale()) {
                this._sounds.playSound(SoundConfig._attack);
            }
            this._attackSprite.setVisible(true);
        } else if (this._attackSprite.isVisible() && this._frame % shootInterval == 0 && !isOffScreen) {
            if (isPlayer) {
                this._attackSprite.moveLeft(6);
            } else if (!isPlayer) {
                this._attackSprite.moveRight(6);
            }
        } else if (isOffScreen) {
            this.changeAnim(isPlayer ? Enum.State.Battling_OpponentReceiveAttack : Enum.State.Battling_PlayerReceiveAttack);
        }
    }

    private void battlePlayerReceiveAttackAnim(boolean isPlayer) {
        boolean hit = !isPlayer && this._attackSprite.getLocX() <= this._opponent.getLocX() + this._opponent.getSizeX() || isPlayer && this._attackSprite.getLocX() >= this._character.getLocX() - this._attackSprite.getSizeX();
        byte interval = this._interval;
        int shootInterval = 5;
        if (this._frame <= 0) {
            this.battleAttackAnimPlayerSetup(isPlayer, true);
            this._attackSprite.setVisible(true);
        } else if (this._frame >= 1 * shootInterval && this._frame % shootInterval == 0 && !hit) {
            if (isPlayer) {
                this._attackSprite.moveRight(6);
            } else {
                this._attackSprite.moveLeft(6);
            }
        } else if (hit) {
            this._attackSprite.setVisible(false);
            this.changeAnim(isPlayer ? Enum.State.Battling_PlayerHit : Enum.State.Battling_OpponentHit);
        }
        if (this._frame % (interval * 2) == 0) {
            if (isPlayer) {
                this._character.drawNumMirror(this._character.getSpriteNum() == 4 ? 0 : 4, false);
            } else {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() == 4 ? 0 : 4, true);
            }
        }
    }

    private void battlePlayerHit(boolean isPlayer) {
        boolean finished = false;
        if (this._frame <= 0) {
            this._frame = 0;
        }
        if (isPlayer ? this._controller.getBattle().getEnemyAttack() > 0 : this._controller.getBattle().getAttack() > 0) {
            finished = this.battleHit(0);
        } else if (isPlayer ? this._controller.getBattle().getEnemyAttack() <= 0 : this._controller.getBattle().getAttack() <= 0) {
            finished = this.dodge(0, isPlayer);
        }
        if (finished) {
            this.changeAnim(isPlayer ? Enum.State.Battling_PlayerHit_Aftermath : Enum.State.Battling_OpponentHit_Aftermath);
        }
    }

    private void battlePlayerHitAftermath(boolean isPlayer) {
        boolean damage;
        Battle battle = this._controller.getBattle();
        boolean bl = isPlayer ? battle.getEnemyAttack() > 0 : (damage = battle.getAttack() > 0);
        if (this._frame <= 0) {
            this.resetScreen();
            this._frame = 0;
            if (isPlayer) {
                this.setupPlayer(false);
                this._character.drawNumMirror(this.getSpriteNum() + (damage ? 10 : 0), false);
            } else {
                this.setupOpponent(false, true);
                this._opponent.drawNumMirror(damage ? 10 : 0, true);
            }
            this._roomEffect.removeIcon();
        } else if (this._frame == this._interval * 6) {
            battle.checkAbsorbsDamage(!isPlayer);
            battle.finishAttack(!isPlayer ? this._controller.getBattle().getEnemyHealth() : this._controller.getBattle().getHealth(), !isPlayer);
            this.setHealthBarSize(isPlayer);
            if (isPlayer && battle.getEnemyAttack() > 0 || !isPlayer && battle.getAttack() > 0) {
                this._sounds.playSound(SoundConfig._battleHPDecrease);
            }
            battle.checkLeechOrSacrificeHealth(isPlayer);
        } else if (this._frame >= this._interval * 10) {
            this.checkBattleEnd(!isPlayer);
        }
    }

    private void checkBattleEnd(boolean isPlayer) {
        Battle battle = this._controller.getBattle();
        AttackEffectProcess process = battle.getProcess();
        battle.checkFinish();
        if (battle.getInProgress()) {
            boolean oppCont;
            if (!(isPlayer || battle.getProcess().getEnemyEffect() != Enum.AttackEffect.Heal && battle.getOppAttack() != Enum.Attribute.None)) {
                process.setEnemyEffect(Enum.AttackEffect.None);
            }
            if (isPlayer && (battle.getProcess().getPlayerEffect() == Enum.AttackEffect.Heal || battle.getAttackType() == Enum.Attribute.None)) {
                process.setPlayerEffect(Enum.AttackEffect.None);
            }
            boolean playerCont = this._controller.getBattle().getPlayerFirst() && isPlayer;
            boolean bl = oppCont = !this._controller.getBattle().getPlayerFirst() && !isPlayer;
            if ((playerCont || oppCont) && (!isPlayer && this._controller.getBattle().getAttack() >= 0 && battle.getAttackType() != Enum.Attribute.None || isPlayer && this._controller.getBattle().getEnemyAttack() >= 0 && battle.getOppAttack() != Enum.Attribute.None)) {
                Enum.State anim = null;
                anim = isPlayer ? (process.getEnemyEffect() == Enum.AttackEffect.Heal ? Enum.State.EnemyHealing : Enum.State.Battling_OpponentAttack) : (process.getPlayerEffect() == Enum.AttackEffect.Heal ? Enum.State.PlayerHealing : Enum.State.Battling_PlayerAttack);
                this.changeAnim(anim);
            } else {
                this._controller.onRoundEnd();
            }
        } else if (this._controller.getBattle().getEnemyHealth() <= 0 && this._controller.getBattle().getBattleType() == Battle.BattleType.PvE_Wild && this._controller.getBattle().getEnemy().getIsZoneBoss()) {
            this._frame = 0;
            this._currentAnim = Enum.State.BossDeath;
            this.zoneBossDeath();
        } else if (this._controller.getBattle().getBattleType() == Battle.BattleType.PvE_Tourney) {
            this.endBattle();
        } else {
            this.endBattle();
        }
    }

    private void heal(boolean isEnemy) {
        if (this._frame <= 0 * this._interval) {
            this._frame = 0;
            this._healthBar.setVisible(true);
            this._healthBarFull.setVisible(true);
            this.setHealthBarSize(!isEnemy);
            if (isEnemy) {
                this.setupOpponent(true, true);
                this._opponent.drawNumMirror(4, true);
                this._opponent.setVisible(true);
            } else {
                this.setupPlayer(true);
                this._character.drawNumMirror(this.getSpriteNum() + 4, false);
                this._character.setVisible(true);
            }
        } else if (this._frame == 7 * this._interval) {
            Battle battle = this._controller.getBattle();
            this._sounds.playSound(SoundConfig._heal);
            if (isEnemy) {
                this._opponent.drawNumMirror(5, true);
            } else {
                this._character.drawNumMirror(this.getSpriteNum() + 5, false);
            }
            battle.checkHeal(isEnemy);
        } else if (this._frame == 17 * this._interval) {
            this.setHealthBarSize(!isEnemy);
            this._sounds.playSound(SoundConfig._battleHPIncrease);
        } else if (this._frame == 27 * this._interval) {
            this.checkBattleEnd(!isEnemy);
        }
    }

    private void endBattle() {
        this._healthBar.setVisible(false);
        this._healthBarFull.setVisible(false);
        this._opponent.setVisible(false);
        this.endAnim();
        this._controller.onBattleEnd();
    }

    private boolean battleHit(int baseFrame) {
        if (this._frame == this._interval * baseFrame) {
            this.resetScreen();
            if (this._attackSprite.getSizeY() == 24 * this.getScale() || this._currentAnim == Enum.State.NPC_Fight) {
                this._sounds.playSound(SoundConfig._attackHit);
            } else if (this._attackSprite.getSizeY() == 48 * this.getScale()) {
                this._sounds.playSound(SoundConfig._strongHit);
            }
            this._opponent.setVisible(false);
            this._character.setVisible(false);
            this._attackSprite.setVisible(false);
            this._healthBar.setVisible(false);
            this._healthBarFull.setVisible(false);
            this._roomEffect.setVisible(true);
            this._roomEffect.setAltIcon("attackHit");
        } else if (this._frame == this._interval * (baseFrame + 1)) {
            this._roomEffect.setAltIcon("attackHitFlash");
        } else if (this._frame == this._interval * (baseFrame + 2)) {
            this._roomEffect.setAltIcon("attackHit");
        } else if (this._frame == this._interval * (baseFrame + 3)) {
            this._roomEffect.setAltIcon("attackHitFlash");
        } else if (this._frame == this._interval * (baseFrame + 4)) {
            this._roomEffect.setAltIcon("attackHit");
        } else if (this._frame == this._interval * (baseFrame + 5)) {
            this._roomEffect.setAltIcon("attackHitFlash");
        }
        return this._frame >= this._interval * (baseFrame + 5);
    }

    private boolean dodge(int baseFrame, boolean isPlayer) {
        boolean doAnim = true;
        if (this._frame == this._interval * baseFrame) {
            this.resetScreen();
            if (isPlayer) {
                this._character.setVisible(true);
            } else {
                this._opponent.setVisible(true);
            }
            this._attackSprite.setVisible(false);
            this._healthBar.setVisible(false);
            this._healthBarFull.setVisible(false);
        }
        if (doAnim) {
            if (this._frame == this._interval * (baseFrame + 1)) {
                if (isPlayer) {
                    this._character.moveRight(3);
                    this._character.moveUp(3);
                } else {
                    this._opponent.moveLeft(3);
                    this._opponent.moveUp(3);
                }
            } else if (this._frame == this._interval * (baseFrame + 2)) {
                if (isPlayer) {
                    this._character.moveRight(3);
                } else {
                    this._opponent.moveLeft(3);
                }
            } else if (this._frame == this._interval * (baseFrame + 4)) {
                if (isPlayer) {
                    this._character.moveRight(3);
                    this._character.moveDown(3);
                } else {
                    this._opponent.moveLeft(3);
                    this._opponent.moveDown(3);
                }
            } else if (this._frame == this._interval * (baseFrame + 6)) {
                if (isPlayer) {
                    this._character.moveLeft(3);
                    this._character.drawNumMirror(this.getSpriteNum() + 1, false);
                } else {
                    this._opponent.moveRight(3);
                    this._opponent.drawNumMirror(1, true);
                }
            } else if (this._frame == this._interval * (baseFrame + 8)) {
                if (isPlayer) {
                    this._character.moveLeft(3);
                    this._character.drawNumMirror(this.getSpriteNum(), false);
                } else {
                    this._opponent.moveRight(3);
                    this._opponent.drawNumMirror(0, true);
                }
            } else if (this._frame == this._interval * (baseFrame + 10)) {
                if (isPlayer) {
                    this._character.moveLeft(3);
                    this._character.drawNumMirror(this.getSpriteNum() + 1, false);
                } else {
                    this._opponent.moveRight(3);
                    this._opponent.drawNumMirror(1, true);
                }
            }
        }
        return this._frame >= this._interval * (baseFrame + 12);
    }

    private void tourneyStart() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.resetFilth();
            this._sounds.playSound(SoundConfig._tourneyStart);
            this._character.setVisible(false);
            PhysicalState digimon = this._controller.getModel().getDigimon();
            Trophy currentTrophy = digimon.getTournament().getTrophy(digimon.getTrophySchedule()[this._trophyInSchedule]);
            this._trophies[0].setLoc(61 - this._xPad, 66 - this._yPad);
            this._trophies[0].setSize(36, 36);
            this._trophies[0].setIcon(this.getTrophySprite(currentTrophy, (byte)(this.getScale() * 4)));
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 1) {
            this._trophies[0].setVisible(false);
        } else if (this._frame == this._interval * 2) {
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 4) {
            this._trophies[0].setVisible(false);
        } else if (this._frame == this._interval * 6) {
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 8) {
            this._trophies[0].setVisible(false);
        } else if (this._frame == this._interval * 10) {
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 13) {
            this._trophies[0].setVisible(false);
        } else if (this._frame == this._interval * 16) {
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 20) {
            this._trophies[0].setVisible(false);
        } else if (this._frame == this._interval * 24) {
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 27) {
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 28) {
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 29) {
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 30) {
            this._roster.setLocX(1);
            this._roster.setLocY(this._mainDisplay.getHeight() / this.getScale());
            this._roster.setVisible(true);
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 31) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 6);
            this._roster.setVisible(true);
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 32) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 6);
            this._roster.setVisible(true);
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 33) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 6);
            this._roster.setVisible(true);
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 34) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 5);
            this._roster.setVisible(true);
            this._trophies[0].setLocY(this._trophies[0].getLocY() / this.getScale() - 6);
            this._trophies[0].setVisible(true);
        } else if (this._frame == this._interval * 35) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 6);
            this._roster.setVisible(true);
        } else if (this._frame == this._interval * 36) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 5);
            this._roster.setVisible(true);
        } else if (this._frame == this._interval * 37) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 5);
            this._roster.setVisible(true);
        } else if (this._frame == this._interval * 38) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 5);
            this._roster.setVisible(true);
        } else if (this._frame == this._interval * 39) {
            this._roster.setLocY(this._roster.getLocY() / this.getScale() - 5);
            this._roster.setVisible(true);
        } else if (this._frame == this._interval * 40) {
            Tournament t = this._controller.getModel().getDigimon().getTournament();
            for (int i = 0; i < t.getRoster().length; ++i) {
                this._participants[i].setSize(16, 16);
                if (t.getRoster()[i] != null) {
                    Icon icon = this.getIndividualIcon(t.getRoster()[i].getOppStage(), t.getRoster()[i].getSpriteSet(), (double)this.getScale() / 3.0, t.getRoster()[i].getSpriteNum(), 0, 48, 48, 12);
                    this._participants[i].setIcon(icon);
                    continue;
                }
                this._participants[i].setSpriteNum(0);
                this._participants[i].setSpriteSheet(this._character.getSpriteSheet());
                this._participants[i].setSpriteLoc(this._character.getSpriteLoc());
                this._participants[i].setIcon(ViewUtil.resizeImage(this._participants[i].getSpriteSheet()[this._participants[i].getSpriteNum()], (double)(this.getScale() / this.getScale()) / 3.0));
            }
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[0].setLocX(this._roster.getLocX() / this.getScale() + 5);
            this._participants[0].setLocY(this._roster.getLocY() / this.getScale() + 2);
            this._participants[0].setVisible(true);
        } else if (this._frame == this._interval * 45) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[1].setLocX(this._roster.getLocX() / this.getScale() + 31);
            this._participants[1].setLocY(this._roster.getLocY() / this.getScale() + 2);
            this._participants[1].setVisible(true);
        } else if (this._frame == this._interval * 50) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[2].setLocX(this._roster.getLocX() / this.getScale() + 57);
            this._participants[2].setLocY(this._roster.getLocY() / this.getScale() + 2);
            this._participants[2].setVisible(true);
        } else if (this._frame == this._interval * 55) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[3].setLocX(this._roster.getLocX() / this.getScale() + 83);
            this._participants[3].setLocY(this._roster.getLocY() / this.getScale() + 2);
            this._participants[3].setVisible(true);
        } else if (this._frame == this._interval * 60) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[4].setLocX(this._roster.getLocX() / this.getScale() + 5);
            this._participants[4].setLocY(this._roster.getLocY() / this.getScale() + 24);
            this._participants[4].setVisible(true);
        } else if (this._frame == this._interval * 65) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[5].setLocX(this._roster.getLocX() / this.getScale() + 31);
            this._participants[5].setLocY(this._roster.getLocY() / this.getScale() + 24);
            this._participants[5].setVisible(true);
        } else if (this._frame == this._interval * 70) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[6].setLocX(this._roster.getLocX() / this.getScale() + 57);
            this._participants[6].setLocY(this._roster.getLocY() / this.getScale() + 24);
            this._participants[6].setVisible(true);
        } else if (this._frame == this._interval * 75) {
            this._sounds.playSound(SoundConfig._populateTourneyRoster);
            this._participants[7].setLocX(this._roster.getLocX() / this.getScale() + 83);
            this._participants[7].setLocY(this._roster.getLocY() / this.getScale() + 24);
            this._participants[7].setVisible(true);
        } else if (this._frame == this._interval * 80) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            PhysicalState digimon = this._controller.getModel().getDigimon();
            Trophy currentTrophy = digimon.getTournament().getTrophy(digimon.getTrophySchedule()[this._trophyInSchedule]);
            this._trophies[0].setLoc(-this._royaleLineup.getSizeX() / this.getScale() / 2 - 9, 3);
            this._trophies[0].setSize(18, 18);
            this._trophies[0].setIcon(this.getTrophySprite(currentTrophy, (byte)(this.getScale() * 2)));
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(-this._royaleLineup.getSizeX() / this.getScale());
            this._royaleLineup.setLocY(0);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 81) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 5);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 5);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 82) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 83) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 84) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 85) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 86) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 87) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 88) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 89) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 90) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 91) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 92) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 93) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 94) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 95) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 96) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 97) {
            for (SpriteObj o : this._participants) {
                o.setLocX(o.getLocX() / this.getScale() + 6);
            }
            this._roster.setLocX(this._roster.getLocX() / this.getScale() + 6);
            this._trophies[0].setLocX(this._trophies[0].getLocX() / this.getScale() + 6);
            this._trophies[0].setVisible(true);
            this._royaleLineup.setLocX(this._royaleLineup.getLocX() / this.getScale() + 6);
            this._royaleLineup.setVisible(true);
        } else if (this._frame == this._interval * 100) {
            this.resetScreen();
            this.endAnim();
            this._controller.setCurrentMenu(Enum.Menu.Royale_Lineup);
            this.drawRoyaleLineup();
        }
    }

    private void tourneyTrophy() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Tournament t = digimon.getTournament();
        if (this._frame <= 0) {
            this._frame = 0;
            this._character.setVisible(false);
            this._opponent.setVisible(false);
            this._trophies[0].setVisible(false);
            this.resetScreen();
            Trophy currentTrophy = t.getCurrentTrophy();
            this._trophies[0].setSize(27, 27);
            int trophyX = (this._trophies[0].getSizeX() / this.getScale() + this._character.getSizeX() / this.getScale() + 3) / 2;
            this._trophies[0].setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - trophyX, -(this._trophies[0].getSizeY() / this.getScale() / 2));
            this._trophies[0].setIcon(this.getTrophySprite(currentTrophy, (byte)(this.getScale() * 3)));
            this._trophies[0].setVisible(true);
            int x = this._trophies[0].getLocX() / this.getScale() + this._trophies[0].getSizeX() / this.getScale() + 3;
            if (t.getIsWon() == 0) {
                Enemy winner = null;
                for (Enemy e : t.getRoster()) {
                    if (e == null || t.getDisqualified().contains(e)) continue;
                    winner = e;
                    break;
                }
                this.setOppSprites(winner);
                this._opponent.setLocX(x);
                this._opponent.drawNumMirror(0, false);
                this._opponent.setVisible(true);
            } else if (t.getIsWon() == 2) {
                this._character.setLocX(x);
                this._character.drawNumMirror(this.getSpriteNum(), false);
                this._character.setVisible(true);
            }
        } else if (this._frame >= this._interval * 1 && this._frame <= 11 * this._interval) {
            if (this._frame % 2 == 0) {
                this._trophies[0].setLocY(1 + this._trophies[0].getLocY() / this.getScale());
            }
        } else if (this._frame == this._interval * 12) {
            this._sounds.playSound(SoundConfig._happy);
            if (t.getIsWon() == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() + 5, false);
            } else if (t.getIsWon() == 2) {
                this._character.drawNumMirror(this.getSpriteNum() + 5, false);
            }
        } else if (this._frame == this._interval * 18) {
            if (t.getIsWon() == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() - 4, false);
            } else if (t.getIsWon() == 2) {
                this._character.drawNumMirror(this.getSpriteNum() + 1, false);
            }
        } else if (this._frame == this._interval * 24) {
            if (t.getIsWon() == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() + 4, false);
            } else if (t.getIsWon() == 2) {
                this._character.drawNumMirror(this.getSpriteNum() + 5, false);
            }
        } else if (this._frame == this._interval * 30) {
            if (t.getIsWon() == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() - 4, false);
            } else if (t.getIsWon() == 2) {
                this._character.drawNumMirror(this.getSpriteNum() + 1, false);
            }
        } else if (this._frame == this._interval * 36) {
            if (t.getIsWon() == 0) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() + 4, false);
            } else if (t.getIsWon() == 2) {
                this._character.drawNumMirror(this.getSpriteNum() + 5, false);
            }
        } else if (this._frame >= this._interval * 42) {
            this.endAnim();
            digimon.setPriorityState(Enum.State.EarningBits_Tourney);
            this._currentAnim = Enum.State.EarningBits_Tourney;
            this.transactionAnim(this._currentAnim);
        }
    }

    private void tourneyEnd() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Tournament t = digimon.getTournament();
        t.setActive(false);
        this.resetScreen();
        this.setSpriteCharDefault();
        this.endAnim();
        this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        if (t.getIsWon() == 2) {
            int id = t.getCurrentTrophy().getItem();
            if (id != -1) {
                Item item = this._controller.getModel().getDigimon().getItems().get(id);
                if (item != null && item.canIncQuantity()) {
                    item.incQuantity();
                    digimon.setUnlockConsumable(id);
                    digimon.setCurrentState(Enum.State.UnlockItem);
                }
            } else {
                FoodType food;
                id = t.getCurrentTrophy().getFood()[0];
                if (id != -1 && (food = this._controller.getModel().getDigimon().getFoodTypes().get(id)) != null && food.canIncQuantity()) {
                    food.incQuantity(t.getCurrentTrophy().getFood()[1]);
                    digimon.setUnlockConsumable(id);
                    digimon.setCurrentState(Enum.State.UnlockFood);
                }
            }
        } else if (t.getIsWon() == 0) {
            digimon.setPraise(true);
        }
        this._controller.onBack();
        digimon.autoSave();
    }

    private String getBitsAsString(int b) {
        String bits = NumberFormat.getIntegerInstance().format(b);
        int length = 8 - bits.length();
        for (int i = 0; i < length; ++i) {
            bits = "  " + bits;
        }
        return bits;
    }

    private void setBitsAnimValues(int current, int bits) {
        this._animValue = current + bits;
        int abs = Math.abs(bits);
        int i = 19 > abs ? abs : 19;
        this._animValue2 = abs / (i > 0 ? i : 1);
        this._animValue3 = abs;
        this._animValue4 = abs % (i > 0 ? i : 1);
        this._bitsPanel.setVisible(true);
        this._bitsLabel.setVisible(true);
    }

    private void setOppSprites(Enemy enemy) {
        SpriteObj o = this.getOppSet(enemy.getOppStage(), enemy.getSpriteSet(), enemy.getSpriteNum());
        this.setOppSprites(o);
    }

    private void setOppSprites(SpriteObj o) {
        this._opponent.setSpriteSheet(o.getSpriteSheet());
        this._opponent.setSpriteSheetMirror(o.getSpriteSheetMirror());
        this._opponent.setSpriteLoc(o.getSpriteLoc());
        this._opponent.setSpriteNum(0);
        if (this._opponent.getSpriteSheet() != null) {
            this._opponent.setIcon(this._opponent.getSpriteSheet()[0]);
        }
    }

    private Icon getEnemyIcon(Enemy enemy, int spriteNum, boolean isMirror) {
        Icon icon;
        SpriteObj o = this.getOppSet(enemy.getOppStage(), enemy.getSpriteSet(), enemy.getSpriteNum());
        if (isMirror) {
            icon = o.getSpriteSheet()[spriteNum];
            icon = ViewUtil.flipIcon(icon);
        } else {
            icon = o.getSpriteSheet()[spriteNum];
        }
        return icon;
    }

    private void npcFight() {
        Tournament t = this._controller.getModel().getDigimon().getTournament();
        this.npcFightAnim(t);
    }

    private void setupNPCFight(Tournament t) {
        this.setSpriteCharDefault();
        this._character.setVisible(false);
        this._character.setIcon(this.getEnemyIcon(t.getRightEnemy(), 4, false));
        this._character.setLocX(82 - this._xPad);
        this._character.setVisible(true);
        this.setOppSprites(t.getLeftEnemy());
        this._opponent.setSize(48, 48);
        this._opponent.setLocY(this._character.getLocY() / this.getScale());
        this._opponent.setLocX(0);
        this._opponent.drawNumMirror(4, true);
        this._opponent.setVisible(true);
    }

    private void npcFightAnim(Tournament t) {
        block24: {
            if (this._frame <= this._interval * 0) {
                this._frame = 0;
                int i = 0;
                try {
                    while (t.getLeftEnemy() == null || t.getRightEnemy() == null) {
                        t.npcFight(i);
                        ++i;
                    }
                    this.setupNPCFight(t);
                }
                catch (IndexOutOfBoundsException exc) {
                    int playerIndex = t.getPlayerIndex();
                    if (t.getIsWon() != 0) {
                        t.clearChecked();
                        this.endAnim();
                        this.setSpriteCharDefault(0);
                        this._controller.setCurrentMenu(Enum.Menu.Royale_Lineup);
                        break block24;
                    }
                    if (t.getDisqualified().size() >= 6 || playerIndex >= 6 && t.getIsWon() == 0) {
                        t.fillChecked();
                        this._frame = 28 * this._interval;
                        break block24;
                    }
                    t.clearChecked();
                    this._frame = -1 * this._interval;
                }
            } else if (this._frame == 7 * this._interval) {
                this._sounds.playSound(SoundConfig._npcFight);
                this._opponent.drawNumMirror(6, true);
                this._opponent.setLocX(0);
                this._character.setIcon(this.getEnemyIcon(t.getRightEnemy(), 6, false));
            } else if (this._frame >= 14 * this._interval && this._frame < 19 * this._interval) {
                this.battleHit(14);
            }
        }
        if (this._frame == 20 * this._interval) {
            this._roomEffect.setVisible(false);
            if (t.getDisqualified().contains(t.getRightEnemy())) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() - 1, true);
                this._opponent.setLocX(0);
                this._character.setIcon(this.getEnemyIcon(t.getRightEnemy(), 10, false));
            } else {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() + 4, true);
                this._opponent.setLocX(0);
                this._character.setIcon(this.getEnemyIcon(t.getRightEnemy(), 5, false));
            }
            this._character.setVisible(true);
            this._opponent.setVisible(true);
        } else if (this._frame >= 29 * this._interval && this._frame <= 60 * this._interval) {
            t.resetEnemies();
            if (!t.isCheckedFull()) {
                this._frame = -1 * this._interval;
                this.npcFightAnim(t);
            } else if (t.getIsWon() != 0) {
                t.clearChecked();
                this.endAnim();
                this.setSpriteCharDefault(0);
                this._controller.setCurrentMenu(Enum.Menu.Royale_Lineup);
            } else if (t.getNPCWon()) {
                this.resetScreen();
                t.clearChecked();
                this.endAnim();
                this.setSpriteCharDefault(0);
                this._controller.getModel().getDigimon().setCurrentState(Enum.State.Tourney_Trophy);
            } else {
                if (this._frame == 29 * this._interval) {
                    this.resetScreen();
                }
                if (this._frame == 60 * this._interval) {
                    t.clearChecked();
                    this.resetScreen();
                    this._frame = -1 * this._interval;
                    this.npcFightAnim(t);
                } else {
                    this.setupRoyaleLineup();
                    this.royaleAnim();
                }
            }
        }
    }

    private void zoneBossDeath() {
        if (this._frame <= this._interval * 0) {
            this._roomEffect.setAltIcon("lightsOff");
            this._roomEffect.setVisible(false);
            this._healthBar.setVisible(false);
            this._healthBarFull.setVisible(false);
            this._opponent.drawNumMirror(10, true);
        } else if (this._frame == this._interval * 8) {
            this._sounds.playSound(SoundConfig._bossDying);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 10) {
            this._roomEffect.setVisible(false);
            this._opponent.setLocX(this._opponent.getLocX() / this.getScale() - 3);
        } else if (this._frame == this._interval * 14) {
            this._opponent.setLocX(this._opponent.getLocX() / this.getScale() + 6);
        } else if (this._frame == this._interval * 16) {
            this._roomEffect.setAltIcon("evol");
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._bossDying);
            this._roomEffect.setVisible(false);
            this._opponent.setLocX(this._opponent.getLocX() / this.getScale() - 6);
        } else if (this._frame == this._interval * 20) {
            this._roomEffect.setAltIcon("lightsOff");
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 22) {
            this._roomEffect.setVisible(false);
            this._opponent.setLocX(this._opponent.getLocX() / this.getScale() + 6);
        } else if (this._frame == this._interval * 24) {
            this._roomEffect.setAltIcon("evol");
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 26) {
            this._opponent.setLocX(this._opponent.getLocX() / this.getScale() - 6);
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 28) {
            this._sounds.playSound(SoundConfig._bossDying);
            this._roomEffect.setAltIcon("lightsOff");
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 30) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 42) {
            this._sounds.playSound(SoundConfig._bossDeath);
            this._opponent.setSizeY(this._opponent.getSizeY() / this.getScale() - 24);
            this._opponent.setLocY(this._opponent.getLocY() / this.getScale() + 24);
        } else if (this._frame == this._interval * 52) {
            this._sounds.playSound(SoundConfig._bossDeath);
            this._opponent.setSizeY(this._opponent.getSizeY() / this.getScale() - 12);
            this._opponent.setLocY(this._opponent.getLocY() / this.getScale() + 12);
        } else if (this._frame == this._interval * 62) {
            this._sounds.playSound(SoundConfig._bossDeath);
            this._opponent.setSizeY(this._opponent.getSizeY() / this.getScale() - 12);
            this._opponent.setLocY(this._opponent.getLocY() / this.getScale() + 12);
        } else if (this._frame == this._interval * 72) {
            this._opponent.setSizeY(48);
            this.endBattle();
        }
    }

    private void zoneChange() {
        WorldMap world = this._controller.getModel().getDigimon().getWorld();
        SpriteObj zoneButton = this._zoneButtons.get(world.getCurrentZone().getZoneNum() - 1);
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this._character.setVisible(false);
            this.drawZoneSelect(false);
            zoneButton.setVisible(true);
            zoneButton.removeIcon();
        } else if (this._frame == this._interval * 5) {
            this._sounds.playSound(SoundConfig._zonePulse);
            zoneButton.setAltIcon("zoneComplete");
        } else if (this._frame == this._interval * 10) {
            zoneButton.removeIcon();
        } else if (this._frame == this._interval * 15) {
            this._sounds.playSound(SoundConfig._zonePulse);
            zoneButton.setAltIcon("zoneComplete");
        } else if (this._frame == this._interval * 20) {
            zoneButton.removeIcon();
        } else if (this._frame == this._interval * 25) {
            this._sounds.playSound(SoundConfig._zonePulse);
            zoneButton.setAltIcon("zoneComplete");
        } else if (this._frame == this._interval * 30) {
            zoneButton.removeIcon();
        } else if (this._frame == this._interval * 35) {
            this._sounds.loopSound(SoundConfig._zonePulseLoop, 2);
            zoneButton.setAltIcon("zoneComplete");
        } else if (this._frame == this._interval * 54) {
            zoneButton.setVisible(false);
            this.resetScreen();
            world.completeZone();
            PhysicalState digimon = this._controller.getModel().getDigimon();
            digimon.setCurrentState(Enum.State.Idling);
            this._currentAnim = Enum.State.None;
            this._frame = this._interval * -1;
            Enemy e = world.getEnemy(this._controller.getPreviousEnemy());
            if (e != null && e.getBossParadeMessage() != null) {
                this._frame = 0;
                this._currentAnim = Enum.State.BossParade;
                this._controller.getModel().getDigimon().setCurrentState(Enum.State.BossParade);
                this.setVictoryMessageText(e.getBossParadeMessage());
                this.bossParade();
            } else {
                this._backgroundAnim.checkBack(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
            }
        }
    }

    private void bossParade() {
        if (this._frame <= this._interval * 0) {
            this._controller.slowClock();
            this._frame = 0;
            this.resetScreen();
            this._menuButton.setVisible(true);
            this._keyboard.setCursorPosition(0);
            this._keyboard.addInteractiveButtons(new SpriteObj[]{this._menuButton});
            this._sounds.playSound(SoundConfig._bossParade, SoundConfig._musicVolume);
            PhysicalState digimon = this._controller.getModel().getDigimon();
            this._character.setVisible(false);
            this._firstBoss.setSize(48, 48);
            this._secondBoss.setSize(48, 48);
            this._thirdBoss.setSize(48, 48);
            this._bosses = digimon.getWorld().getCurrentMapBosses();
            this._boss1 = this.getNextBoss(digimon);
            this._boss2 = this.getNextBoss(digimon);
            this._boss3 = this.getNextBoss(digimon);
            SpriteObj obj = this.getOppSet(this._boss1.getNewStage(), this._boss1.getNewSpriteSet(), this._boss1.getNewSpriteNum());
            this._firstBoss.setSpriteNum(0);
            this._firstBoss.setSpriteSheet(obj.getSpriteSheet());
            this._firstBoss.setSpriteLoc(obj.getSpriteLoc());
            obj = this.getOppSet(this._boss2.getNewStage(), this._boss2.getNewSpriteSet(), this._boss2.getNewSpriteNum());
            this._secondBoss.setSpriteNum(0);
            this._secondBoss.setSpriteSheet(obj.getSpriteSheet());
            this._secondBoss.setSpriteLoc(obj.getSpriteLoc());
            obj = this.getOppSet(this._boss3.getNewStage(), this._boss3.getNewSpriteSet(), this._boss3.getNewSpriteNum());
            this._thirdBoss.setSpriteNum(0);
            this._thirdBoss.setSpriteSheet(obj.getSpriteSheet());
            this._thirdBoss.setSpriteLoc(obj.getSpriteLoc());
            this._firstBoss.setLoc(135 - this._xPad, 62 - this._yPad);
            this._secondBoss.setLoc(186 - this._xPad, 62 - this._yPad);
            this._thirdBoss.setLoc(237 - this._xPad, 62 - this._yPad);
        } else if (this._frame == this._interval * 5) {
            this._firstBoss.moveLeft(3);
            this._secondBoss.moveLeft(3);
            this._thirdBoss.moveLeft(3);
            if (this._boss1 != null) {
                this._firstBoss.drawNumMirror(9, false);
            }
            if (this._boss2 != null) {
                this._secondBoss.drawNumMirror(9, false);
            }
            if (this._boss3 != null) {
                this._thirdBoss.drawNumMirror(9, false);
            }
        } else if (this._frame == this._interval * 10) {
            this._firstBoss.moveLeft(3);
            this._secondBoss.moveLeft(3);
            this._thirdBoss.moveLeft(3);
            if (this._boss1 != null) {
                this._firstBoss.drawNumMirror(10, false);
            }
            if (this._boss2 != null) {
                this._secondBoss.drawNumMirror(10, false);
            }
            if (this._boss3 != null) {
                this._thirdBoss.drawNumMirror(10, false);
            }
            this._frame = 0;
        }
        this.checkBossOverflow(this._controller.getModel().getDigimon());
        if (this._boss1 != null) {
            this._firstBoss.setVisible(true);
        }
        if (this._boss2 != null) {
            this._secondBoss.setVisible(true);
        }
        if (this._boss3 != null) {
            this._thirdBoss.setVisible(true);
        }
        this.checkEndBossAnim();
    }

    private void checkEndBossAnim() {
        if (this._boss1 == null && this._boss2 == null && this._boss3 == null && this._thirdBoss.getLocX() / this.getScale() < -21 - this._xPad) {
            this._firstBoss.setLocX(500);
            this._secondBoss.setLocX(500);
            this._thirdBoss.setLocX(500);
            this._frame = 0;
            this._currentAnim = Enum.State.MapComplete;
            this.mapComplete();
        }
    }

    private void checkBossOverflow(PhysicalState digimon) {
        SpriteObj obj;
        if (this._firstBoss.getLocX() + this._firstBoss.getSizeX() < 0) {
            this._boss1 = this.getNextBoss(digimon);
            if (this._boss1 != null) {
                this._firstBoss.setLoc(this._thirdBoss.getLocX() / this.getScale() + this._thirdBoss.getSizeX() / this.getScale() + 3, 62 - this._yPad);
                obj = this.getOppSet(this._boss1.getNewStage(), this._boss1.getNewSpriteSet(), this._boss1.getNewSpriteNum());
                this._firstBoss.setSpriteNum(0);
                this._firstBoss.setSpriteSheet(obj.getSpriteSheet());
                this._firstBoss.setSpriteLoc(obj.getSpriteLoc());
            } else {
                this._firstBoss.setVisible(false);
            }
        }
        if (this._secondBoss.getLocX() + this._secondBoss.getSizeX() < 0) {
            this._boss2 = this.getNextBoss(digimon);
            if (this._boss2 != null) {
                this._secondBoss.setLoc(this._firstBoss.getLocX() / this.getScale() + this._firstBoss.getSizeX() / this.getScale() + 3, 62 - this._yPad);
                obj = this.getOppSet(this._boss2.getNewStage(), this._boss2.getNewSpriteSet(), this._boss2.getNewSpriteNum());
                this._secondBoss.setSpriteNum(0);
                this._secondBoss.setSpriteSheet(obj.getSpriteSheet());
                this._secondBoss.setSpriteLoc(obj.getSpriteLoc());
            } else {
                this._secondBoss.setVisible(false);
            }
        }
        if (this._thirdBoss.getLocX() + this._thirdBoss.getSizeX() < 0) {
            this._boss3 = this.getNextBoss(digimon);
            if (this._boss3 != null) {
                this._thirdBoss.setLoc(this._secondBoss.getLocX() / this.getScale() + this._secondBoss.getSizeX() / this.getScale() + 3, 62 - this._yPad);
                obj = this.getOppSet(this._boss3.getNewStage(), this._boss3.getNewSpriteSet(), this._boss3.getNewSpriteNum());
                this._thirdBoss.setSpriteNum(0);
                this._thirdBoss.setSpriteSheet(obj.getSpriteSheet());
                this._thirdBoss.setSpriteLoc(obj.getSpriteLoc());
            } else {
                this._thirdBoss.setVisible(false);
            }
        }
    }

    private EvolutionInfo getNextBoss(PhysicalState digimon) {
        EvolutionInfo boss = null;
        for (int i = 0; i < this._bosses.length; ++i) {
            if (this._bosses[i] == -1) continue;
            boss = digimon.getEvolution().getDigimon(this._bosses[i]);
            this._bosses[i] = -1;
            break;
        }
        return boss;
    }

    private void mapComplete() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            PhysicalState digimon = this._controller.getModel().getDigimon();
            this._character.setLocX(135 - this._xPad);
            this._character.setVisible(true);
            EvolutionInfo d = digimon.getEvolution().getDigimon(digimon.getIndex());
            if (d.getVaccineNum() > -1) {
                this.checkAttackSprite(Enum.Attribute.Vaccine, digimon.getVaccinePower(), false, d.getVaccineNum());
            } else if (d.getDataNum() > -1) {
                this.checkAttackSprite(Enum.Attribute.Data, digimon.getDataPower(), false, d.getDataNum());
            } else if (d.getVirusNum() > -1) {
                this.checkAttackSprite(Enum.Attribute.Virus, digimon.getVirusPower(), false, d.getVirusNum());
            } else {
                switch (digimon.getAttribute()) {
                    case Data: {
                        this.checkAttackSprite(Enum.Attribute.Data, digimon.getDataPower(), false, d.getDataNum());
                        break;
                    }
                    case Vaccine: {
                        this.checkAttackSprite(Enum.Attribute.Vaccine, digimon.getVaccinePower(), false, d.getVaccineNum());
                        break;
                    }
                    case Virus: {
                        this.checkAttackSprite(Enum.Attribute.Virus, digimon.getVirusPower(), false, d.getVirusNum());
                        break;
                    }
                    default: {
                        this.checkAttackSprite(Enum.Attribute.Vaccine, digimon.getVaccinePower(), false, d.getVaccineNum());
                    }
                }
            }
            this._attackSprite.setLocX(500);
            this.doubleAttack(this._attackSprite);
        } else if (this._frame == this._interval * 1) {
            int currentNum = this._character.getSpriteNum();
            int spriteNum = this.getSpriteNum();
            int num = 0;
            this._character.moveLeft(3);
            num = currentNum == spriteNum + 1 ? spriteNum : spriteNum + 1;
            this._character.drawNumMirror(num, false);
            if (this._character.getLocX() > this._mainDisplay.getWidth() / 2 - this._character.getSizeX() / 2) {
                this._frame = 0;
            }
        } else if (this._frame == this._interval * 3) {
            this._sounds.playSound(SoundConfig._strongAttack);
            this._character.drawNumMirror(6, false);
            this._attackSprite.setVisible(true);
            this._attackSprite.setLocX(this._character.getLocX() / this.getScale() - this._attackSprite.getSizeX() / this.getScale());
        } else if (this._frame == this._interval * 4) {
            this._attackSprite.moveLeft(3);
            if (this._attackSprite.getLocX() > 27 * this.getScale() - this._xPad * this.getScale() - this._attackSprite.getSizeX() / 2) {
                this._frame = this._interval * 3;
            }
        } else if (this._frame >= this._interval * 5 && this._frame <= this._interval * 10) {
            this._attackSprite.setLocX(500);
            this.battleHit(5);
        } else if (this._frame == this._interval * 11) {
            this._character.setVisible(true);
            this._roomEffect.setVisible(false);
            this._victoryMessage.setVisible(true);
            this._victoryMessage.setLocX(this._mainDisplay.getWidth() / this.getScale() + this._victoryMessage.getSizeX() / (2 * this.getScale()));
        } else if (this._frame == this._interval * 12) {
            int currentNum = this._character.getSpriteNum();
            int spriteNum = this.getSpriteNum();
            int num = 0;
            this._victoryMessage.moveLeft(3);
            this._character.moveLeft(3);
            num = currentNum == spriteNum + 1 ? spriteNum : spriteNum + 1;
            this._character.drawNumMirror(num, false);
            if (this._character.getLocX() > -this._character.getSizeX()) {
                this._frame = this._interval * 11;
            }
        } else if (this._frame == this._interval * 13) {
            this._victoryMessage.moveLeft(3);
            if (this._victoryMessage.getLocX() > this._mainDisplay.getWidth() / (2 * this.getScale()) - this._victoryMessage.getSizeX() / (3 * this.getScale()) - (this.getScale() == 3 ? -1 : (this.getScale() == 2 ? 8 : 22)) + this._xPad * this.getScale() / (2 * this.getScale())) {
                this._frame = this._interval * 12;
            }
        } else if (this._frame == this._interval * 33) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            digimon.setCurrentState(Enum.State.Idling);
            this.setSpriteCharDefault();
            this._currentAnim = Enum.State.None;
            this._frame = this._interval * -1;
            this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        }
    }

    private void checkAttackSprite(Enum.Attribute attribute, int value, boolean isMirror, int attackNum) {
        Icon s;
        this._attackSprite.setIsMirror(isMirror);
        if (attackNum <= -1 || attackNum >= this._specialAttacks.getSpriteSheet().length) {
            value = value >= 600 ? 600 : value;
            int calc = (int)Math.floor(value / 25);
            switch (attribute) {
                case Vaccine: {
                    this._attackSprite.setSpriteNum(0 + calc);
                    break;
                }
                case Data: {
                    this._attackSprite.setSpriteNum(25 + calc);
                    break;
                }
                case Virus: {
                    this._attackSprite.setSpriteNum(50 + calc);
                }
            }
            s = this._attackSprite.getIsMirror() ? ViewUtil.flipIcon(this._attackSprite.getSpriteSheet()[this._attackSprite.getSpriteNum()]) : this._attackSprite.getSpriteSheet()[this._attackSprite.getSpriteNum()];
        } else {
            s = this._attackSprite.getIsMirror() ? ViewUtil.flipIcon(this._specialAttacks.getSpriteSheet()[attackNum]) : this._specialAttacks.getSpriteSheet()[attackNum];
        }
        this._attackSprite.setIcon(s);
    }

    private void trainingAnimPrep(Enum.Attribute attribute) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._emotionLabel.removeIcon();
        this._roomEffect.removeIcon();
        this._opponent.setSpriteSheet(this._battleBags.getSpriteSheet());
        this._opponent.setSpriteLoc(this._battleBags.getSpriteLoc());
        this._character.setVisible(false);
        this._success = false;
        this._opponent.setLocX(26 - this._xPad);
        this._opponent.setLocY(56 - this._yPad);
        this._opponent.setSizeX(20);
        this._opponent.setSizeY(58);
        this._trainBarFull.setSizeX(0);
        this._attackSprite.setSizeX(24);
        this._attackSprite.setSizeY(24);
        this._attackSprite.setLocX(-100);
        this._attackSprite.setLocY(this._character.getLocY() / this.getScale());
        switch (attribute) {
            case Vaccine: {
                this.vaccinePrePrep();
                this.checkAttackSprite(attribute, digimon.getVaccinePower(), false, -1);
                break;
            }
            case Virus: {
                this.virusPrePrep();
                this.checkAttackSprite(attribute, digimon.getVirusPower(), false, -1);
                break;
            }
            case Data: {
                this.dataPrePrep();
                this.checkAttackSprite(attribute, digimon.getDataPower(), true, -1);
            }
        }
    }

    private void vaccinePrePrep() {
        this._menuRect.setVisible(true);
        this._character.setLocX(100 - this._xPad);
        this._character.setSizeX(30);
        this._hitButton.setLocX(70 - this._xPad);
        this._hitButton.setLocY(85 - this._yPad);
        this._hitButton.setAltIcon("trainButton");
        this._attackSprite.setIcon(this._attackSprite.getSpriteSheet()[0]);
        this._opponent.setAltIcon("punchingBag");
        this._hitLabel.setVisible(true);
        this._hitButton.setVisible(true);
        this._backButton.setVisible(true);
        try {
            Robot r = new Robot();
            r.mouseMove(this._hitButton.getLocationOnScreen().x + this._hitButton.getSizeX() / 2 + 3, this._hitButton.getLocationOnScreen().y + this._hitButton.getSizeY() / 4);
        }
        catch (AWTException ex) {
            Logger.getLogger(SpriteAnim.class.getName()).log(Level.SEVERE, null, ex);
        }
        catch (IllegalComponentStateException illegalComponentStateException) {
            // empty catch block
        }
    }

    private void dataPrePrep() {
        this._menuRect.setVisible(true);
        this._character.setLocX(105 - this._xPad);
        this._shieldTop.setAltIcon("trainShield");
        this._shieldBot.setAltIcon("shieldTransp");
        this._attackSprite.setIcon(this._attackSprite.getSpriteSheet()[25]);
        this._opponent.setAltIcon("trainGreen");
        this._opponent.setSizeX(32);
        this._opponent.setSizeY(28);
        this._opponent.setLocY(85 - this._yPad);
        this._up = false;
        this._started = false;
        this._character.setVisible(true);
        this._opponent.setVisible(true);
        this._backButton.setVisible(true);
        this._shieldTop.setVisible(true);
        this._shieldBot.setVisible(true);
    }

    private void virusPrePrep() {
        this._menuRect.setVisible(true);
        this._character.setLocX(100 - this._xPad);
        this._character.setSizeX(30);
        this._hitButton.setLocX(70 - this._xPad);
        this._hitButton.setLocY(85 - this._yPad);
        this._hitButton.setAltIcon("trainButton");
        this._attackSprite.setIcon(this._attackSprite.getSpriteSheet()[50]);
        this._opponent.setAltIcon("punchingBag");
        this._trainBar.setVisible(true);
        this._trainBarFull.setVisible(true);
        this._hitButton.setVisible(true);
        this._backButton.setVisible(true);
        try {
            Robot r = new Robot();
            r.mouseMove(this._hitButton.getLocationOnScreen().x + this._hitButton.getSizeX() / 2, this._hitButton.getLocationOnScreen().y + this._hitButton.getSizeY() / 4);
        }
        catch (AWTException ex) {
            Logger.getLogger(SpriteAnim.class.getName()).log(Level.SEVERE, null, ex);
        }
        catch (IllegalComponentStateException illegalComponentStateException) {
            // empty catch block
        }
    }

    private void preTraining(Enum.Attribute attribute) {
        switch (attribute) {
            case Vaccine: {
                this.drawVaccinePre();
                break;
            }
            case Data: {
                this.drawDataPre();
                break;
            }
            case Virus: {
                this.drawVirusPre();
            }
        }
    }

    private void hideAttributeIconsExcept(Enum.Attribute a) {
        this._border.setVisible(false);
        switch (a) {
            case Vaccine: {
                this._dataAttack.setVisible(false);
                this._virusAttack.setVisible(false);
                break;
            }
            case Data: {
                this._vaccineAttack.setVisible(false);
                this._virusAttack.setVisible(false);
                break;
            }
            case Virus: {
                this._vaccineAttack.setVisible(false);
                this._dataAttack.setVisible(false);
                break;
            }
            default: {
                this._vaccineAttack.setVisible(false);
                this._dataAttack.setVisible(false);
                this._virusAttack.setVisible(false);
            }
        }
    }

    private void drawHPTrainingAttackSuccess() {
        if (this._frame <= 0) {
            this._frame = 0;
            this._menuRect.setVisible(false);
            this.hideAttributeIconsExcept(Enum.Attribute.values()[this._controller.getBarSize()]);
            this._character.drawNum(6);
            this._sounds.playSound(SoundConfig._attack);
        } else if (this.battleHit(1 * this._interval)) {
            this.endAnim();
            this._controller.getModel().getDigimon().setPriorityState(Enum.State.HP_Training);
        }
    }

    private void drawHPTrainingAttackFail() {
        if (this._frame <= 0) {
            this._frame = 0;
            this._menuRect.setVisible(false);
            this.hideAttributeIconsExcept(Enum.Attribute.None);
            this._character.drawNum(9);
            this._opponent.drawNum(this.getBattleBagSprite(Enum.Attribute.values()[this._controller.getNumHits()]) + 1);
            this._sounds.playSound(SoundConfig._attack);
        } else if (this.battleHit(1 * this._interval)) {
            this.endAnim();
            this._controller.getModel().getDigimon().setPriorityState(Enum.State.HP_Training);
        }
    }

    private void drawHPTraining() {
        if (this._controller.getTrainingRound() < Config._hpTrainingRounds && this._controller.getTrainingRoundsWon() < Config._hpTrainingRoundsWon) {
            byte frame;
            int rank = this._controller.getModel().getDigimon().getFullHealthPoints() / Config._hpTrainDifficultyChange;
            switch (rank) {
                case 0: {
                    frame = Config._hpTrainingRoundLengthEasy;
                    break;
                }
                case 1: {
                    frame = Config._hpTrainingRoundLength;
                    break;
                }
                default: {
                    frame = Config._hpTrainingRoundLengthHard;
                }
            }
            if (this._frame <= 0) {
                this._frame = 0;
                this.resetScreen();
                this._menuRect.setVisible(true);
                this._success = false;
                if (this._longClip == null) {
                    this._longClip = this._sounds.loopSound(SoundConfig._trainTimer, SoundConfig._masterVolume);
                }
                Random r = new Random();
                int i = r.nextInt(3);
                this._controller.setNumHits(i);
                this.setSpriteCharDefault();
                this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() - this._character.getWidth() / this.getScale() + 9);
                this._character.drawNumMirror(0, false);
                this._character.setVisible(true);
                this.setBattleBags();
                this._opponent.setLocY(this._character.getLocY() / this.getScale() - 3);
                this._opponent.setLocX(0);
                this._opponent.drawNumMirror(this.getBattleBagSprite(Enum.Attribute.values()[i]), true);
                this._opponent.setVisible(true);
                this._vaccineAttack.setLocX(this._character.getLocX() / this.getScale() - this._vaccineAttack.getWidth() / this.getScale() - 4);
                this._vaccineAttack.setLocY(this._character.getLocY() / this.getScale() - 6);
                this._vaccineAttack.setVisible(true);
                this._dataAttack.setLocX(this._vaccineAttack.getLocX() / this.getScale());
                this._dataAttack.setLocY(this._vaccineAttack.getLocY() / this.getScale() + this._vaccineAttack.getHeight() / this.getScale() + 6);
                this._dataAttack.setVisible(true);
                this._virusAttack.setLocX(this._vaccineAttack.getLocX() / this.getScale());
                this._virusAttack.setLocY(this._dataAttack.getLocY() / this.getScale() + this._dataAttack.getHeight() / this.getScale() + 6);
                this._virusAttack.setVisible(true);
                this._gameButton.setIsEnabled(true);
                this._keyboard.addInteractiveButtons(new SpriteObj[]{this._gameButton, this._vaccineAttack, this._dataAttack, this._virusAttack});
                this._keyboard.setCursorPosition(0);
            } else if (this._frame >= frame * this._interval) {
                this._keyboard.clearInteractiveButtons();
                this._controller.onHPTrainingAttribute(Enum.Attribute.None);
            }
        } else {
            this._success = this._controller.getTrainingRoundsWon() >= Config._hpTrainingRoundsWon;
            this.finishTraining(Enum.Attribute.None);
        }
    }

    private void drawVaccinePre() {
        if (this._frame <= this._interval * 0) {
            this.trainingAnimPrep(Enum.Attribute.Vaccine);
            this._character.setVisible(false);
            if (this._keyboard.getInteractiveButtons().isEmpty()) {
                this._keyboard.addInteractiveButtons(new SpriteObj[]{this._hitButton, this._backButton});
                this._keyboard.setCursorPosition(0);
            }
            this._frame = 0;
        }
        if (this._frame == this._interval * 30) {
            this._backButton.setVisible(false);
            if (!this._keyboard.getInteractiveButtons().isEmpty()) {
                try {
                    this._keyboard.getInteractiveButtons().remove(this._backButton);
                }
                catch (ArrayIndexOutOfBoundsException arrayIndexOutOfBoundsException) {
                    // empty catch block
                }
                this._keyboard.setCursorPosition(0);
            }
            this._frame = this._interval * 31;
        }
        if (this._frame == this._interval * 41) {
            this.endAnim();
            this._controller.onPreFinish(Enum.Attribute.Vaccine);
        }
    }

    private void drawDataPre() {
        int small = 3;
        int big = 6;
        int frame = 1;
        int rank = this._controller.getModel().getDigimon().getDataPower() / Config._attributeTrainDifficultyChange;
        switch (rank) {
            case 0: {
                frame = Config._dataTrainShootFrameEasy;
                break;
            }
            case 1: {
                frame = Config._dataTrainShootFrame;
                break;
            }
            default: {
                frame = Config._dataTrainShootFrameHard;
            }
        }
        int pad = 6;
        int offset = pad * 8;
        if (this._frame % (this._interval * 2) == 0) {
            this._character.drawNumMirror(this._character.getSpriteNum() == 4 ? 1 : 4, false);
        }
        if (this._frame <= this._interval * 0) {
            this.trainingAnimPrep(Enum.Attribute.Data);
            if (this._keyboard.getInteractiveButtons().isEmpty()) {
                this._keyboard.setCursorPosition(0);
                this._keyboard.addInteractiveButtons(new SpriteObj[]{this._shieldTop, this._backButton});
            }
            this._attackSprite.setVisible(false);
            this._character.drawNumMirror(1, false);
            this._frame = 0;
        } else if (this._frame == frame + pad) {
            this._opponent.setAltIcon("trainGreenUp");
        } else if (this._frame == frame * 2 + pad * 2) {
            this._opponent.setAltIcon("trainGreen");
        } else if (this._frame == frame * 3 + pad * 3) {
            this._opponent.setAltIcon("trainGreenUp");
        } else if (this._frame == frame * 4 + pad * 4) {
            this._opponent.setAltIcon("trainGreen");
        } else if (this._frame == frame * 5 + pad * 5) {
            this._opponent.setAltIcon("trainGreenUp");
        } else if (this._frame == frame * 6 + pad * 6) {
            this._opponent.setAltIcon("trainGreen");
        } else if (this._frame == frame * 7 + pad * 7) {
            this._opponent.setAltIcon("trainGreenUp");
        } else if (this._frame == frame * 8 + pad * 8) {
            this._attackSprite.setLocX(55 - this._xPad);
            this._attackSprite.setSizeX(1);
            this._attackSprite.setSizeY(1);
            Random random = new Random();
            int r = random.nextInt(2);
            if (r == 0) {
                this._opponent.setAltIcon("trainGreen");
                this._attackSprite.setLocY(84 - this._yPad);
                this._up = false;
            }
            if (r == 1) {
                this._opponent.setAltIcon("trainGreenUp");
                this._attackSprite.setLocY(77 - this._yPad);
                this._up = true;
            }
            this._attackSprite.setVisible(true);
        } else if (this._frame == frame * 9 + offset) {
            this._backButton.setVisible(false);
            if (!this._keyboard.getInteractiveButtons().isEmpty()) {
                try {
                    this._keyboard.getInteractiveButtons().remove(this._backButton);
                }
                catch (ArrayIndexOutOfBoundsException arrayIndexOutOfBoundsException) {
                    // empty catch block
                }
                this._keyboard.setCursorPosition(0);
            }
            this._attackSprite.setSizeX(big);
            this._attackSprite.setSizeY(big);
        } else if (this._frame == frame * 10 + offset) {
            this._attackSprite.setSizeX(small);
            this._attackSprite.setSizeY(big);
        } else if (this._frame == frame * 11 + offset) {
            this._attackSprite.setSizeX(big);
            this._attackSprite.setSizeY(big);
        } else if (this._frame == frame * 12 + offset) {
            this._attackSprite.setSizeX(small);
            this._attackSprite.setSizeY(big);
        } else if (this._frame == frame * 13 + offset) {
            this._attackSprite.setSizeX(big);
            this._attackSprite.setSizeY(big);
        } else if (this._frame == frame * 14 + offset) {
            this._started = true;
            this._attackSprite.setVisible(false);
            this.endAnim();
            this._controller.onPreFinish(Enum.Attribute.Data);
        }
    }

    private void checkShield() {
        boolean shieldTop = this._controller.getShieldActiveTop();
        if (shieldTop) {
            this._shieldTop.setAltIcon("trainShield");
            this._shieldBot.setAltIcon("shieldTransp");
        } else {
            this._shieldBot.setAltIcon("trainShield");
            this._shieldTop.setAltIcon("shieldTransp");
        }
        this._shieldTop.setVisible(true);
        this._shieldBot.setVisible(true);
    }

    private void drawVirusPre() {
        byte frame;
        int rank = this._controller.getModel().getDigimon().getVirusPower() / Config._attributeTrainDifficultyChange;
        switch (rank) {
            case 0: {
                frame = Config._virusGameBarSpeedEasy;
                break;
            }
            case 1: {
                frame = Config._virusGameBarSpeed;
                break;
            }
            default: {
                frame = Config._virusGameBarSpeedHard;
            }
        }
        int maxBar = 94 * this.getScale();
        this._character.setVisible(false);
        if (this._frame < 1) {
            this.trainingAnimPrep(Enum.Attribute.Virus);
            if (this._keyboard.getInteractiveButtons().isEmpty()) {
                this._keyboard.setCursorPosition(0);
                this._keyboard.addInteractiveButtons(new SpriteObj[]{this._hitButton, this._backButton});
            }
            this._frame = 1;
        }
        if (this._frame == frame) {
            if (this._trainBarFull.getSizeX() < maxBar) {
                this._trainBarFull.setSizeX(this._trainBarFull.getSizeX() / this.getScale() + 4);
                this._controller.setBarSize(this._trainBarFull.getSizeX() / this.getScale());
            } else if (this._trainBarFull.getSizeX() >= maxBar) {
                this._trainBarFull.setSizeX(0);
            }
            this._frame = 1;
        }
    }

    private void attackAnim() {
        if (this.checkTrainingAttribute() == Enum.Attribute.Data) {
            this.attackGreen();
        } else {
            this.attackDefault();
        }
    }

    private void attackDefault() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this._character.drawNumMirror(this.getSpriteNum() + 6, false);
            this._attackSprite.setLocX(85 - this._xPad);
            this._attackSprite.setVisible(true);
            this._character.setVisible(true);
            this._opponent.setVisible(true);
            if (this._success) {
                this._sounds.playSound(SoundConfig._strongAttack);
                this.doubleAttack(this._attackSprite);
            } else {
                this._sounds.playSound(SoundConfig._attack);
                this._attackSprite.setSizeY(24);
            }
        } else if (this._frame == this._interval * 1) {
            this._attackSprite.setLocX(81 - this._xPad);
        } else if (this._frame == this._interval * 2) {
            this._attackSprite.setLocX(75 - this._xPad);
        } else if (this._frame == this._interval * 3) {
            this._attackSprite.setLocX(69 - this._xPad);
        } else if (this._frame == this._interval * 4) {
            this._attackSprite.setLocX(63 - this._xPad);
        } else if (this._frame == this._interval * 5) {
            this._attackSprite.setLocX(57 - this._xPad);
        } else if (this._frame == this._interval * 6) {
            this._attackSprite.setLocX(51 - this._xPad);
        } else if (this._frame == this._interval * 7) {
            this._character.setVisible(false);
            this.endAnim();
            this._controller.onAttackEnd();
        }
    }

    private void attackGreen() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this._menuRect.setVisible(false);
            this._character.setVisible(true);
            this._opponent.setVisible(true);
            this._shieldTop.setVisible(true);
            this._shieldBot.setVisible(true);
            this._attackSprite.setLocX(55 - this._xPad);
            this._attackSprite.setSizeX(24);
            this._attackSprite.setSizeY(24);
            if (this._up) {
                this._attackSprite.setLocY(55 - this._yPad);
            } else {
                this._attackSprite.setLocY(80 - this._yPad);
            }
            this._attackSprite.setVisible(true);
        } else if (this._frame == this._interval * 1) {
            this._sounds.playSound(SoundConfig._turretShoot);
            this._attackSprite.setLocX(61 - this._xPad);
        } else if (this._frame == this._interval * 2) {
            this._attackSprite.setLocX(67 - this._xPad);
        } else if (this._frame == this._interval * 3) {
            this._character.setVisible(false);
            this.endAnim();
            this._controller.onAttackEnd();
        }
    }

    private void hitAnim() {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this._frame = 0;
            if (this._attackSprite.getSizeY() == 24 * this.getScale()) {
                this._sounds.playSound(SoundConfig._attackHit);
            } else if (this._attackSprite.getSizeY() == 48 * this.getScale()) {
                this._sounds.playSound(SoundConfig._strongHit);
            }
            this._roomEffect.setAltIcon("attackHit");
        } else if (this._frame == this._interval * 1) {
            this._roomEffect.setAltIcon("attackHitFlash");
        } else if (this._frame == this._interval * 2) {
            this._roomEffect.setAltIcon("attackHit");
        } else if (this._frame == this._interval * 3) {
            this._roomEffect.setAltIcon("attackHitFlash");
        } else if (this._frame == this._interval * 4) {
            this._roomEffect.setAltIcon("attackHit");
        } else if (this._frame == this._interval * 5) {
            this._roomEffect.setAltIcon("attackHitFlash");
        } else if (this._frame == this._interval * 6) {
            this._roomEffect.removeIcon();
            this.endAnim();
            this._controller.onHitEnd();
        }
        this._roomEffect.setVisible(true);
    }

    private void attackAftermath() {
        if (this.checkTrainingAttribute() == Enum.Attribute.Data) {
            this.aftermathGreen();
        } else {
            this.aftermathDefault();
        }
    }

    private void aftermathDefault() {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this._frame = 0;
            this._character.setVisible(true);
            this._opponent.setVisible(true);
            if (this._success) {
                this._opponent.setAltIcon("punchingBagBroken");
                this._character.drawNumMirror(this.getSpriteNum(), false);
            } else {
                this._character.drawNumMirror(this.getSpriteNum() + 10, false);
            }
        } else if (this._frame == this._interval * 16) {
            this.finishTraining(this.checkTrainingAttribute());
        }
    }

    private void aftermathGreen() {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this._frame = 0;
            this._character.setVisible(true);
            this._opponent.setVisible(true);
            this._shieldTop.setVisible(true);
            this._shieldBot.setVisible(true);
            if (!this._success) {
                this._character.drawNumMirror(this.getSpriteNum() + 10, true);
            } else {
                this._character.drawNumMirror(this.getSpriteNum(), true);
            }
        } else if (this._frame == this._interval * 16) {
            this.finishTraining(this.checkTrainingAttribute());
        }
    }

    private void finishTraining(Enum.Attribute a) {
        this.setupMainMenuAndInteractiveButtons();
        this._opponent.removeIcon();
        this.endAnim();
        this._controller.onExerciseFinish(a);
        this.setSpriteCharDefault();
        this.resetScreen();
    }

    private void winning() {
        if (this._frame == this._interval * 30) {
            this._roomEffect.removeIcon();
        }
        this.cheer(true, SoundConfig._win, false);
        if (this._frame <= 0 && this._currentAnim == Enum.State.Winning) {
            this.drawBattleEndIcons(this._emotionLabel.getAltSprite("happy"));
            this._emotionLabel.setVisible(false);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 6) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 12) {
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 18) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 24) {
            this._roomEffect.setVisible(true);
        }
    }

    private void losing() {
        if (this._frame == this._interval * 30) {
            this._washLabel.setVisible(true);
        } else if (this._frame > this._interval * 31 && this._washLabel.getLocX() > -this._washLabel.getWidth()) {
            this._washLabel.moveLeft(2);
            if (this._washLabel.getLocX() <= this._character.getLocX() + this._character.getWidth() + this._emotionLabel.getWidth()) {
                this._character.moveLeft(2);
                this._roomEffect.moveLeft(2);
            }
        } else if (this._frame > this._interval * 31) {
            this._roomEffect.setVisible(false);
            this._roomEffect.setLocX(26 - this._xPad);
            this._washLabel.setVisible(false);
            this._character.setVisible(false);
            this.setSpriteCharDefault();
            this.endAnim();
        } else {
            this.jeer(this._controller.getModel().getDigimon().getDisposition() < 0, SoundConfig._lose, false);
            if (this._frame <= 0 && this._currentAnim == Enum.State.Losing) {
                this.drawBattleEndIcons(this._emotionLabel.getAltSprite("dying"));
                this._washLabel.setLocX(this._mainDisplay.getWidth() / this.getScale());
                this._emotionLabel.setVisible(false);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 6) {
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 12) {
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 18) {
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 24) {
                this._roomEffect.setVisible(true);
            }
        }
    }

    private boolean adjustBehindCharacter(SpriteObj o) {
        int x;
        boolean mirror = false;
        int n = x = this._character.getIsMirror() ? this._character.getLocX() - o.getWidth() : this._character.getLocX() + this._character.getWidth();
        if (x < 0 || x > this._mainDisplay.getWidth() + o.getWidth()) {
            x = !this._character.getIsMirror() ? this._character.getLocX() - o.getWidth() : this._character.getLocX() + this._character.getWidth();
            mirror = true;
        }
        o.setLocX(x / this.getScale());
        return mirror;
    }

    private void birthdayDrop(int index) {
        if (this._frame <= 0) {
            this._animValue = 0;
            this._frame = 0;
            this.resetScreen();
            this._character.drawNum(0);
            if (this._character.getX() < -(this._character.getWidth() / 2) || this._character.getX() > this._mainDisplay.getWidth() + this._character.getWidth() / 2) {
                this.setSpriteCharDefault();
            }
            if (this.adjustBehindCharacter(this._foodLabel)) {
                this._character.drawNumMirror(0, !this._character.getIsMirror());
            }
            this.adjustBehindCharacter(this._emotionLabel);
            this._foodLabel.setLocY(-this._foodLabel.getHeight() / this.getScale());
            this._foodLabel.setIcon(this._inventoryButton.getAltSprite("inventory"));
            this._foodLabel.setVisible(true);
        } else if (!(this._animValue == 0 && this.moveDownToTarget(this._foodLabel, this._mainDisplay.getHeight() - this._foodLabel.getHeight()) || this._animValue <= 0)) {
            if (this._frame == this._animValue + 1 * this._interval) {
                this._foodLabel.moveUp(1);
                if (this._character.getIsMirror()) {
                    this._foodLabel.moveLeft(1);
                } else {
                    this._foodLabel.moveRight(1);
                }
            } else if (this._frame == this._animValue + 2 * this._interval) {
                this._sounds.playSound(SoundConfig._flyTransportFall);
                this._foodLabel.moveDown(1);
                if (this._character.getIsMirror()) {
                    this._foodLabel.moveLeft(1);
                } else {
                    this._foodLabel.moveRight(1);
                }
            } else if (this._frame == this._animValue + 8 * this._interval) {
                this._sounds.playSound(SoundConfig._attention);
                this._emotionLabel.setAltIcon("attention");
                this._emotionLabel.setVisible(true);
                this._character.drawNum(8);
            } else if (this._frame == this._animValue + 14 * this._interval) {
                this._emotionLabel.removeIcon();
                this._character.drawNum(1);
            } else if (this._frame == this._animValue + 20 * this._interval) {
                this._character.drawNumMirror(0, !this._character.getIsMirror());
            } else if (this._frame == this._animValue + 26 * this._interval) {
                this._character.drawNum(5);
            } else if (this._frame == this._animValue + 32 * this._interval) {
                this._character.drawNum(1);
            } else if (this._frame == this._animValue + 38 * this._interval) {
                this._sounds.playSound(SoundConfig._unlockConsumable);
                this.setFoodSet(this._controller.getModel().getDigimon().getFoodTypes().get(index));
                this._foodLabel.drawNum(0);
            } else if (this._frame == this._animValue + 40 * this._interval) {
                this._foodLabel.setIcon(this._inventoryButton.getAltSprite("inventory"));
            } else if (this._frame == this._animValue + 42 * this._interval) {
                this._foodLabel.drawNum(0);
            } else if (this._frame == this._animValue + 44 * this._interval) {
                this._foodLabel.setIcon(this._inventoryButton.getAltSprite("inventory"));
            } else if (this._frame == this._animValue + 48 * this._interval) {
                this._foodLabel.drawNum(0);
            } else if (this._frame == this._animValue + 52 * this._interval) {
                this._foodLabel.setIcon(this._inventoryButton.getAltSprite("inventory"));
            } else if (this._frame == this._animValue + 56 * this._interval) {
                this._foodLabel.drawNum(0);
            } else if (this._frame == this._animValue + 64 * this._interval) {
                this._character.drawNum(5);
            } else if (this._frame == this._animValue + 72 * this._interval) {
                this._controller.getModel().getDigimon().setUnlockConsumable(-1);
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            }
        }
    }

    private boolean moveDownToTarget(SpriteObj o, int target) {
        if (o.getLocY() < target) {
            o.setLocY(o.getLocY() / this.getScale() + 2);
            if (o.getLocY() >= target) {
                o.setLocY(target / this.getScale());
                this._animValue = this._frame;
                this._sounds.playSound(SoundConfig._flyTransportFall);
                return false;
            }
            return true;
        }
        return false;
    }

    private void wakeUp(int sprite, boolean isFilth) {
        int rate = 5;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (isFilth) {
            this.checkFilth(digimon);
            this.stateNumTic(digimon, false);
        }
        if (this._frame <= 0) {
            this._frame = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            if (isFilth) {
                this.adjustCharacterForFilth();
            }
            this._character.drawNumMirror(2, false);
            this._character.setVisible(true);
        } else if (this._frame == this._interval * 2 * rate) {
            this._character.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 4 * rate) {
            this._character.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 6 * rate) {
            this._character.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 8 * rate) {
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 9 * rate) {
            this._character.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 10 * rate) {
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 11 * rate) {
            this._character.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 12 * rate) {
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 13 * rate) {
            this._character.drawNumMirror(sprite, false);
        } else if (this._frame == this._interval * 15 * rate) {
            this.endAnim();
        }
    }

    private void cheer(boolean goodPraise, String sound, boolean isFilth) {
        int downPraise;
        int upPraise;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Enum.Stage s = digimon.getGrowthStage();
        int n = s == Enum.Stage.Egg ? 0 : (upPraise = goodPraise ? 5 : 6);
        int n2 = s == Enum.Stage.Egg ? 1 : (downPraise = goodPraise ? 7 : 4);
        if (isFilth) {
            this.checkFilth(digimon);
            this.stateNumTic(digimon, false);
        }
        if (this._frame <= this._interval * 0) {
            this._stateNum = 0;
            this._frame = 0;
            this.resetScreen();
            this.setSpriteCharDefault();
            if (isFilth) {
                this.adjustCharacterForFilth();
            }
            this._sounds.playSound(sound);
            this._emotionLabel.setVisible(true);
            this._emotionLabel.setAltIcon("happy");
            this._character.drawNumMirror(this.getSpriteNum() + upPraise, false);
            this._character.setVisible(true);
        } else if (this._frame == this._interval * 6) {
            this._emotionLabel.removeIcon();
            this._character.drawNumMirror(this.getSpriteNum() + downPraise, false);
        } else if (this._frame == this._interval * 12) {
            this._emotionLabel.setAltIcon("happy");
            this._character.drawNumMirror(this.getSpriteNum() + upPraise, false);
        } else if (this._frame == this._interval * 18) {
            this._emotionLabel.removeIcon();
            this._character.drawNumMirror(this.getSpriteNum() + downPraise, false);
        } else if (this._frame == this._interval * 24) {
            this._emotionLabel.setAltIcon("happy");
            this._character.drawNumMirror(this.getSpriteNum() + upPraise, false);
        } else if (this._frame == this._interval * 30) {
            this._emotionLabel.removeIcon();
            this._character.drawNumMirror(this.getSpriteNum(), false);
            this.endAnim();
        }
    }

    private void badHealthJeer() {
        this.jeer(false, SoundConfig._badHealthJeer, "dying", "dying2", true);
    }

    private void jeer(boolean goodScold, String sound, boolean isFilth) {
        this.jeer(goodScold, sound, "unhappy", "unhappy2", isFilth);
    }

    private void jeer(boolean goodScold, String sound, String icon, String icon2, boolean isFilth) {
        int downScold;
        int upScold;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Enum.Stage s = digimon.getGrowthStage();
        int n = s == Enum.Stage.Egg ? 0 : (upScold = goodScold ? 6 : 9);
        int n2 = s == Enum.Stage.Egg ? 1 : (downScold = goodScold ? 4 : 10);
        if (isFilth) {
            this.checkFilth(digimon);
            this.stateNumTic(digimon, false);
        }
        if (this._frame <= this._interval * 0) {
            this._stateNum = 0;
            this._frame = 0;
            this.resetScreen();
            this.disableMainMenu();
            this.setSpriteCharDefault();
            if (isFilth) {
                this.adjustCharacterForFilth();
            }
            this._emotionLabel.setAltIcon(icon);
            this._emotionLabel.setVisible(true);
            this._character.drawNumMirror(this.getSpriteNum() + downScold, false);
            this._character.setVisible(true);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(sound);
            this._emotionLabel.setAltIcon(icon2);
            this._character.drawNumMirror(this.getSpriteNum() + upScold, false);
        } else if (this._frame == this._interval * 12) {
            this._emotionLabel.setAltIcon(icon);
            this._character.drawNumMirror(this.getSpriteNum() + downScold, false);
        } else if (this._frame == this._interval * 18) {
            this._emotionLabel.setAltIcon(icon2);
            this._character.drawNumMirror(this.getSpriteNum() + upScold, false);
        } else if (this._frame == this._interval * 24) {
            this._emotionLabel.setAltIcon(icon);
            this._character.drawNumMirror(this.getSpriteNum() + downScold, false);
        } else if (this._frame == this._interval * 30) {
            this._emotionLabel.removeIcon();
            this._character.drawNumMirror(this.getSpriteNum(), false);
            this.endAnim();
        }
    }

    private void retreat(boolean sad) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this.animFilth();
        this.stateNumTic(digimon, false);
        if (this._frame <= 0) {
            this._sounds.playSound(SoundConfig._retreatScramble);
            this._frame = 0;
            this.setSpriteCharDefault();
            this._character.moveRight(20);
            this._character.drawNumMirror(1, true);
            this._character.setVisible(true);
            this._filthLabel.setVisible(false);
            this._opponent.setLocX((double)(-(this._opponent.getSizeX() / this.getScale())) / 1.7);
            this._opponent.setVisible(true);
        } else if (this._frame == 1 * this._interval) {
            this._character.moveLeft(1);
            this._character.moveUp(1);
            this._character.drawNumMirror(0, true);
        } else if (this._frame == 2 * this._interval) {
            this._character.moveLeft(1);
            this._character.moveUp(1);
            this._character.drawNumMirror(1, true);
        } else if (this._frame == 3 * this._interval) {
            this._character.moveLeft(1);
            this._character.moveDown(1);
            this._character.drawNumMirror(0, true);
        } else if (this._frame == 4 * this._interval) {
            this._character.moveLeft(1);
            this._character.moveDown(1);
            this._character.drawNumMirror(1, true);
        } else if (this._frame == 5 * this._interval) {
            this._character.drawNumMirror(sad ? 9 : 6, true);
            if (digimon.getBMGauge() > digimon.getBMMax() && digimon.getDisposition() != -1 && this._controller.getBattle().getHealth() <= this._controller.getBattle().getFullHealth() / 3) {
                this._stateNum = 0;
                this._filthLabel.setVisible(true);
                byte f = digimon.poop(false);
                this.playPoopSound(f);
                this._filthLabel.setLocX(this._character.getLocX() / this.getScale() - 30);
                this.drawFilthLevel(new byte[]{f}, 1);
            }
        } else if (this._frame > 7 * this._interval && this._frame % (this._interval * 1) == 0 && (double)this._character.getLocX() < (double)this._mainDisplay.getWidth() + (double)this._character.getSizeX() * 1.9) {
            if (this._frame == 8 * this._interval) {
                this._sounds.playSound(SoundConfig._retreatDash);
            }
            this._character.moveRight(6);
            this._character.drawNumMirror(this._character.getSpriteNum() == 0 ? 1 : 0, true);
        } else if ((double)this._character.getLocX() >= (double)this._mainDisplay.getWidth() + (double)this._character.getSizeX() * 1.9) {
            this.resetFilth();
            this.endAnim();
            digimon.setCurrentState(sad ? Enum.State.Sad_Jeering : Enum.State.Jeering);
            this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
        }
        if (this._frame % (this._interval * 3) == 0) {
            if ((double)this._character.getLocX() >= (double)this._mainDisplay.getWidth() + (double)this._character.getSizeX() * 0.5) {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() == 5 ? 7 : 5, true);
            } else {
                this._opponent.drawNumMirror(this._opponent.getSpriteNum() == 6 ? 4 : 6, true);
            }
        }
    }

    private void yawning() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
        } else if (this._frame == this._interval * 4) {
            this._character.drawNumMirror(this.getSpriteNum() + 8, this._character.getIsMirror());
        } else if (this._frame == this._interval * 10) {
            this._character.setLocX(this._character.getLocX() / this.getScale() - 3);
        } else if (this._frame == this._interval * 16) {
            this._character.setLocX(this._character.getLocX() / this.getScale() + 3);
        } else if (this._frame == this._interval * 22) {
            this._character.setLocX(this._character.getLocX() / this.getScale() - 3);
        } else if (this._frame == this._interval * 28) {
            this._character.setLocX(this._character.getLocX() / this.getScale() + 3);
        } else if (this._frame == this._interval * 33) {
            this._character.drawNumMirror(this.getSpriteNum() + 3, this._character.getIsMirror());
        } else if (this._frame == this._interval * 38) {
            this._character.drawNumMirror(this.getSpriteNum() + 1, this._character.getIsMirror());
        } else if (this._frame == this._interval * 43) {
            this._character.drawNumMirror(this.getSpriteNum() + 3, this._character.getIsMirror());
        } else if (this._frame == this._interval * 48) {
            this._character.drawNumMirror(this.getSpriteNum() + 1, this._character.getIsMirror());
        } else if (this._frame == this._interval * 53) {
            this.endSpecialIdleAnim();
        }
        this._character.setVisible(true);
    }

    private void weathering() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        byte isRain = digimon.checkIsRain();
        boolean niceWeather = digimon.checkNiceWeather(isRain);
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
        } else if (this._frame == this._interval * 3) {
            if (niceWeather) {
                this._character.drawNumMirror(this.getSpriteNum() + 5, this._character.getIsMirror());
            } else if (isRain == 1) {
                this._character.drawNumMirror(this.getSpriteNum() + 4, this._character.getIsMirror());
            } else if (isRain == 0) {
                this._character.drawNumMirror(this.getSpriteNum() + 9, this._character.getIsMirror());
                this._character.moveLeft(3);
            }
        } else if (this._frame == this._interval * 6) {
            if (niceWeather) {
                this._character.drawNumMirror(this.getSpriteNum() + 3, this._character.getIsMirror());
            } else if (isRain == 1) {
                this._character.drawNumMirror(this.getSpriteNum() + 4, !this._character.getIsMirror());
            } else if (isRain == 0) {
                this._character.moveRight(3);
            }
        } else if (this._frame == this._interval * 9) {
            if (niceWeather) {
                this._character.drawNumMirror(this.getSpriteNum() + 5, this._character.getIsMirror());
            } else if (isRain == 1) {
                this._character.drawNumMirror(this.getSpriteNum() + 4, !this._character.getIsMirror());
            } else if (isRain == 0) {
                this._character.moveLeft(3);
            }
        } else if (this._frame == this._interval * 12) {
            if (niceWeather) {
                this._character.drawNumMirror(this.getSpriteNum() + 3, this._character.getIsMirror());
            } else if (isRain == 1) {
                this._character.drawNumMirror(this.getSpriteNum() + 4, !this._character.getIsMirror());
            } else if (isRain == 0) {
                this._character.moveRight(3);
            }
        } else if (this._frame == this._interval * 15) {
            this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
        } else if (this._frame == this._interval * 18) {
            this.endSpecialIdleAnim();
        }
        this._character.setVisible(true);
    }

    private void surprising() {
        PhysicalState myDigimon = this._controller.getModel().getDigimon();
        int disposition = myDigimon.getDisposition();
        boolean isUnwell = this._controller.setIdleType();
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
        } else if (this._frame == this._interval * 7) {
            switch (disposition) {
                case -1: {
                    this._character.drawNumMirror(this.getSpriteNum() + 4, this._character.getIsMirror());
                    break;
                }
                case 0: {
                    this._character.drawNumMirror(this.getSpriteNum() + 6, this._character.getIsMirror());
                    break;
                }
                case 1: {
                    this._character.drawNumMirror(this.getSpriteNum() + 9, this._character.getIsMirror());
                }
            }
        } else if (this._frame == this._interval * 14) {
            switch (disposition) {
                case -1: {
                    this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
                    break;
                }
                case 0: {
                    this._character.drawNumMirror(this.getSpriteNum() + 4, this._character.getIsMirror());
                    break;
                }
                case 1: {
                    this._character.drawNumMirror(this.getSpriteNum() + 10, this._character.getIsMirror());
                }
            }
        } else if (this._frame == this._interval * 21) {
            switch (disposition) {
                case -1: {
                    this._character.drawNumMirror(this.getSpriteNum() + 4, this._character.getIsMirror());
                    break;
                }
                case 0: {
                    this._character.drawNumMirror(this.getSpriteNum() + 6, this._character.getIsMirror());
                    break;
                }
                case 1: {
                    this._character.drawNumMirror(this.getSpriteNum() + 9, this._character.getIsMirror());
                }
            }
        } else if (this._frame == this._interval * 28) {
            switch (disposition) {
                case -1: {
                    this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
                    break;
                }
                case 0: {
                    this._character.drawNumMirror(this.getSpriteNum() + 4, this._character.getIsMirror());
                    break;
                }
                case 1: {
                    this._character.drawNumMirror(this.getSpriteNum() + 10, this._character.getIsMirror());
                }
            }
        } else if (this._frame == this._interval * 35) {
            this._character.drawNumMirror(this.getSpriteNum(), this._character.getIsMirror());
        } else if (this._frame == this._interval * 42) {
            this.endSpecialIdleAnim();
        }
        this._character.setVisible(true);
    }

    private void personalityMooding(Enum.Mood m) {
        int frame;
        PhysicalState myDigimon = this._controller.getModel().getDigimon();
        int disposition = myDigimon.getDisposition();
        int n = myDigimon.getRestless() > 0 ? 5 : (frame = myDigimon.getRestless() < 0 ? 7 : 6);
        if (this._frame <= 0) {
            this._character.setLocY(63 - this._yPad);
            this._frame = 0 * this._interval;
        } else if (this._frame == frame * this._interval) {
            this._character.drawNumMirror(this._character.getSpriteNum() == 0 ? 1 : 0, this._character.getIsMirror());
        }
        block0 : switch (disposition) {
            case -1: {
                switch (m) {
                    case Happy: {
                        this.personalityMoodHappyNegative(frame);
                        break;
                    }
                    case Unhappy: {
                        this.personalityMoodAngryNegative(frame);
                    }
                }
                break;
            }
            case 0: {
                switch (m) {
                    case Happy: {
                        this.personalityMoodHappyNeutral(frame);
                        break;
                    }
                    case Unhappy: {
                        this.personalityMoodAngryNeutral(frame);
                    }
                }
                break;
            }
            case 1: {
                switch (m) {
                    case Happy: {
                        this.personalityMoodHappyPositive(frame);
                        break block0;
                    }
                    case Unhappy: {
                        this.personalityMoodAngryPositive(frame);
                    }
                }
            }
        }
        this._character.setVisible(true);
    }

    private void personalityMoodHappyPositive(int start) {
        if (this._frame == this._interval * (start * 2)) {
            this._character.drawNumMirror(7, false);
        } else if (this._frame == this._interval * (start * 3)) {
            this._character.drawNumMirror(5, this._character.getIsMirror());
            this._character.moveUp(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * (start * 4)) {
            this._character.drawNumMirror(7, this._character.getIsMirror());
            this._character.moveDown(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * (start * 5)) {
            this._character.drawNumMirror(5, !this._character.getIsMirror());
            this._character.moveUp(3);
            this._character.moveRight(3);
        } else if (this._frame == this._interval * (start * 6)) {
            this._character.drawNumMirror(7, this._character.getIsMirror());
            this._character.moveDown(3);
            this._character.moveRight(3);
        } else if (this._frame == this._interval * (start * 7)) {
            this._character.drawNumMirror(5, !this._character.getIsMirror());
            this._character.moveUp(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * (start * 8)) {
            this._character.drawNumMirror(7, this._character.getIsMirror());
            this._character.moveDown(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * (start * 9)) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
            this._character.moveRight(3);
        } else if (this._frame >= this._interval * (start * 10)) {
            this.endSpecialIdleAnim();
        }
    }

    private void personalityMoodHappyNegative(int start) {
        if (this._frame == this._interval * (start * 2)) {
            this._character.drawNumMirror(7, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 3)) {
            this._character.drawNumMirror(5, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 4)) {
            this._character.drawNumMirror(7, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 5)) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * (start * 6)) {
            this.endSpecialIdleAnim();
        }
    }

    private void personalityMoodHappyNeutral(int start) {
        if (this._frame == this._interval * (start * 2)) {
            this._character.drawNumMirror(7, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 3)) {
            this._character.drawNumMirror(5, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 4)) {
            this._character.drawNumMirror(7, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 5)) {
            this._character.drawNumMirror(5, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 6)) {
            this._character.drawNumMirror(7, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 7)) {
            this._character.drawNumMirror(5, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 8)) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * (start * 9)) {
            this.endSpecialIdleAnim();
        }
    }

    private void personalityMoodAngryNeutral(int start) {
        if (this._frame == this._interval * (start * 2)) {
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 3)) {
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 4)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 5)) {
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 6)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 7)) {
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 8)) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * (start * 9)) {
            this.endSpecialIdleAnim();
        }
    }

    private void personalityMoodAngryPositive(int start) {
        if (this._frame == this._interval * (start * 2)) {
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 3)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 4)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 5)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 6)) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * (start * 7)) {
            this.endSpecialIdleAnim();
        }
    }

    private void personalityMoodAngryNegative(int start) {
        if (this._frame == this._interval * (start * 2)) {
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 3)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 4)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 5)) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 6)) {
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 7)) {
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 8)) {
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 9)) {
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 10)) {
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * (start * 11)) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * (start * 12)) {
            this.endSpecialIdleAnim();
        }
    }

    private void tantrum() {
        if (this._frame <= 0) {
            this._character.setLocY(63 - this._yPad);
            this._frame = 0;
            this._character.drawNumMirror(1, this._character.getIsMirror());
        } else if (this._frame == this._interval * 5) {
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * 10) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 15) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 20) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 25) {
            this._character.drawNumMirror(4, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 30) {
            this._character.drawNumMirror(1, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 35) {
            this._character.moveUp(3);
            this._character.drawNumMirror(6, this._character.getIsMirror());
        } else if (this._frame == this._interval * 40) {
            this._character.moveDown(3);
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * 45) {
            this._character.moveUp(3);
            this._character.drawNumMirror(6, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 50) {
            this._character.moveDown(3);
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * 55) {
            this._character.moveUp(3);
            this._character.drawNumMirror(6, !this._character.getIsMirror());
        } else if (this._frame == this._interval * 60) {
            this._character.moveDown(3);
            this._character.drawNumMirror(4, this._character.getIsMirror());
        } else if (this._frame == this._interval * 65) {
            this._character.drawNumMirror(0, !this._character.getIsMirror());
        } else if (this._frame >= this._interval * 70) {
            this.endSpecialIdleAnim();
        }
        this._character.setVisible(true);
    }

    private boolean isAdd(Enum.State s) {
        switch (s) {
            case Buying_Food: 
            case Buying_Habitat: 
            case Buying_Item: {
                return false;
            }
            case Selling_Food: 
            case Selling_Item: 
            case EarningBits_Tourney: 
            case EarningBits: {
                return true;
            }
        }
        return false;
    }

    private void transactionAnim(Enum.State s) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (this._frame <= this._interval * 0) {
            boolean add = this.isAdd(s);
            int price = 0;
            switch (s) {
                case Buying_Habitat: {
                    price = digimon.getHabitats().get(this._habitat).getPrice() * this.getPurchaseAmount();
                    break;
                }
                case Buying_Food: 
                case Buying_Item: {
                    price = this._consumableType.getPurchasePrice() * this.getPurchaseAmount();
                    break;
                }
                case Selling_Food: 
                case Selling_Item: {
                    price = this._consumableType.getResellPrice() * this.getPurchaseAmount();
                    break;
                }
                case EarningBits: {
                    this.resetScreen();
                    price = this._controller.getNumHits();
                    if (price > 0) break;
                    this.endAnim();
                    return;
                }
                case EarningBits_Tourney: {
                    this.resetScreen();
                    price = digimon.getTournament().getBits();
                    if (price > 0) break;
                    this.tourneyEnd();
                    return;
                }
            }
            this._menuRect.setVisible(true);
            this.drawPurchaseScreen(price, add ? "+" : "-");
            this.setBitsAnimValues(digimon.getBits(), add ? price : -price);
            this._frame = 2 * this._interval;
        } else if (this._frame == 13 && digimon.getBits() != this._animValue && this._animValue4 > 0) {
            boolean add = this.isAdd(s);
            this._sounds.playSound(add ? SoundConfig._addBits : SoundConfig._subtractBits);
            digimon.setBits(digimon.getBits() + (add ? this._animValue4 : -this._animValue4));
            this._animValue3 -= this._animValue4;
            this.drawPurchaseScreen(this._animValue3, add ? "+" : "-");
            this._animValue4 = 0;
            this._frame = this._interval * 2;
        } else if (this._frame == 13 && digimon.getBits() != this._animValue && this._animValue4 == 0) {
            boolean add = this.isAdd(s);
            this._sounds.playSound(add ? SoundConfig._addBits : SoundConfig._subtractBits);
            digimon.setBits(digimon.getBits() + (add ? this._animValue2 : -this._animValue2));
            this._animValue3 -= this._animValue2;
            this.drawPurchaseScreen(this._animValue3, add ? "+" : "-");
            this._frame = this._interval * 2;
        } else if (this._frame == 12 * this._interval && digimon.getBits() == this._animValue) {
            this.endAnim();
            switch (s) {
                case Buying_Food: {
                    this._foodType.incQuantity(this.getPurchaseAmount());
                    this._consumableType.decStock(this.getPurchaseAmount());
                    this._controller.setCurrentMenu(Enum.Menu.Food_Shop);
                    break;
                }
                case Buying_Item: {
                    this._itemType.incQuantity(this.getPurchaseAmount());
                    this._consumableType.decStock(this.getPurchaseAmount());
                    this._controller.setCurrentMenu(Enum.Menu.Item_Shop);
                    break;
                }
                case Buying_Habitat: {
                    digimon.getHabitats().get(this._habitat).setUnlocked(true);
                    this._controller.setCurrentMenu(Enum.Menu.Habitat_Shop);
                    this._backgroundAnim.checkBackNoAnim(digimon, this._controller.getCurrentMenu(), this.getScale(), this._controller.getBattle());
                    break;
                }
                case Selling_Food: {
                    this._foodType.decQuantity(this.getPurchaseAmount() * this._foodType.getUsesPerConsumable());
                    this.setConsumablePage(Enum.Menu.Food_Inventory_Sell, this._consumablePage);
                    this._controller.setCurrentMenu(Enum.Menu.Food_Inventory_Sell);
                    break;
                }
                case Selling_Item: {
                    this._itemType.decQuantity(this.getPurchaseAmount() * this._itemType.getUsesPerConsumable());
                    this.setConsumablePage(Enum.Menu.Item_Inventory_Sell, this._consumablePage);
                    this._controller.setCurrentMenu(Enum.Menu.Item_Inventory_Sell);
                    break;
                }
                case EarningBits: {
                    this.resetScreen();
                    break;
                }
                case EarningBits_Tourney: {
                    this.tourneyEnd();
                }
            }
            this._menuRect.setVisible(false);
            digimon.autoSave();
        }
    }

    private void unlockingDNA(Enum.Field f) {
        if (this._frame <= this._interval * 0) {
            this._controller.slowClock();
            this._frame = 0;
            this.resetScreen();
            this._menuRect.setVisible(true);
            this.checkField(f);
            this._character.setVisible(false);
            this._fieldLabel.setLoc(this._mainDisplay.getWidth() / this.getScale() / 4 - this._fieldLabel.getSizeX() / this.getScale() / 4, 8);
            this._fieldLabel.setVisible(false);
            this.drawConsumableUnlockIcon(this._digisoulButton.getAltSprites().get(1));
        } else if (this._frame == this._interval * 1) {
            this._sounds.playSound(SoundConfig._unlockDNA);
        } else if (this._frame == this._interval * 3) {
            this._fieldLabel.setVisible(true);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 4) {
            this._fieldLabel.setVisible(false);
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 6) {
            this._fieldLabel.setVisible(true);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 8) {
            this._fieldLabel.setVisible(false);
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 10) {
            this._fieldLabel.setVisible(true);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 12) {
            this._fieldLabel.setVisible(false);
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 15) {
            this._fieldLabel.setVisible(true);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 18) {
            this._fieldLabel.setVisible(false);
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 22) {
            this._fieldLabel.setVisible(true);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 26) {
            this._fieldLabel.setVisible(false);
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 31) {
            this._fieldLabel.setVisible(true);
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 41) {
            this._fieldLabel.setVisible(false);
            this._controller.getModel().getDigimon().setUnlockConsumable(-1);
            this._menuRect.setVisible(false);
            this.endAnim();
        }
    }

    private void drawConsumableUnlockIcon(Icon i) {
        BufferedImage consumable = new BufferedImage(this._roomEffect.getWidth(), this._roomEffect.getHeight(), 2);
        Graphics2D g2 = consumable.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        BufferedImage bag = ViewUtil.createBuffImage(this._inventoryButton.getAltSprites().get(0));
        int x = this._roomEffect.getWidth() - bag.getWidth() - 1 * this.getScale();
        int y = this._roomEffect.getHeight() - bag.getHeight();
        g2.drawImage(bag, null, x, y);
        int max = 16 * this.getScale();
        if (i.getIconHeight() > max || i.getIconWidth() > max) {
            i = ViewUtil.resizeImage(i, max, max);
        }
        BufferedImage type = ViewUtil.createBuffImage(i);
        x = x - type.getWidth() - 1 * this.getScale();
        y = y + bag.getHeight() / 2 - type.getHeight() / 2;
        g2.drawImage(type, null, x, y);
        g2.dispose();
        this._roomEffect.setIcon(new ImageIcon(consumable));
    }

    private void unlocking(boolean isItem, int index) {
        if (index > -1) {
            if (this._frame <= this._interval * 0) {
                this._controller.slowClock();
                this.resetScreen();
                this._menuRect.setVisible(true);
                this._frame = 0;
                this._character.setVisible(false);
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
                if (isItem) {
                    if (index >= 0 && index < this._controller.getModel().getDigimon().getItems().size()) {
                        this._itemType = this._controller.getModel().getDigimon().getItems().get(index);
                        boolean itemEvol = this._itemType.getAnim() == Enum.State.ItemEvol;
                        this._itemLabel.setLoc(66 - this._xPad - (itemEvol ? 10 : 0), 63 - this._yPad);
                        this.setItemSet();
                        this._itemLabel.setIcon(this._itemLabel.getSpriteSheet()[itemEvol ? 1 : 0]);
                        if (itemEvol) {
                            this.drawConsumableUnlockIcon(this._digisoulButton.getAltSprites().get(1));
                        } else {
                            EvolutionInfo mon = this._controller.getModel().getDigimon().getEvolution().getDigimon(29);
                            Icon i = this.getIndividualIcon(mon.getNewStage(), mon.getNewSpriteSet(), (double)this.getScale() * 0.33, mon.getNewSpriteNum(), 0, 48, 48, 12);
                            this.drawConsumableUnlockIcon(i);
                        }
                    }
                } else if (index >= 0 && index < this._controller.getModel().getDigimon().getFoodTypes().size()) {
                    this._itemLabel.setLoc(66 - this._xPad, 63 - this._yPad);
                    this._foodType = this._controller.getModel().getDigimon().getFoodTypes().get(index);
                    this.setFoodSet();
                    this._itemLabel.setIcon(this._foodLabel.getSpriteSheet()[0]);
                    this.drawConsumableUnlockIcon(this._feedButton.getAltSprites().get(1));
                }
            } else if (this._frame == this._interval * 1) {
                this._sounds.playSound(SoundConfig._unlockConsumable);
            } else if (this._frame == this._interval * 3) {
                this._itemLabel.setVisible(true);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 4) {
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 6) {
                this._itemLabel.setVisible(true);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 8) {
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 10) {
                this._itemLabel.setVisible(true);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 12) {
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 15) {
                this._itemLabel.setVisible(true);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 18) {
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 22) {
                this._itemLabel.setVisible(true);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 26) {
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
            } else if (this._frame == this._interval * 31) {
                this._itemLabel.setVisible(true);
                this._roomEffect.setVisible(true);
            } else if (this._frame == this._interval * 41) {
                this._itemLabel.setVisible(false);
                this._roomEffect.setVisible(false);
                this._menuRect.setVisible(false);
                this._controller.getModel().getDigimon().setUnlockConsumable(-1);
                this.endAnim();
                if (index == 32) {
                    if (this._controller.getModel().getDigimon().getItems().get(index).getCurrentUses() > 0) {
                        this.setMessage("You can only have one Digimemory");
                        this._controller.setCurrentMenu(Enum.Menu.DigiMemory_Validation);
                    } else {
                        this._controller.getModel().getDigimon().setNewDigimemory();
                    }
                }
            }
        } else {
            this.endAnim();
        }
    }

    private void perfectWinsInc() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            int perfectWins = this._controller.getModel().getDigimon().getPerfectWins() - 1;
            this.resetScreen();
            this._menuRect.setVisible(true);
            this.checkHealthTracker(perfectWins);
        } else if (this._frame == this._interval * 12) {
            int perfectWins = this._controller.getModel().getDigimon().getPerfectWins();
            this._sounds.playSound(SoundConfig._perfectWinsInc);
            this.checkHealthTracker(perfectWins);
        } else if (this._frame == this._interval * 24) {
            this.resetScreen();
            this.endAnim();
        }
    }

    private void healthInc() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this._menuRect.setVisible(true);
            this.checkHealthTracker(Config._perfectWinsLimit - 1);
        } else if (this._frame == this._interval * 12) {
            this._sounds.playSound(SoundConfig._perfectWinsInc);
            this._healthUp.drawNumMirror(5, false);
            this._healthUp.setVisible(true);
        } else if (this._frame == this._interval * 24) {
            this.resetScreenExceptMenuRect();
            PhysicalState digimon = this._controller.getModel().getDigimon();
            this.setupDataHP(digimon.getHealthPoints(), digimon.getFullHealthPoints() - 1);
            this._healthBarFull.setVisible(true);
            this._healthBar.setVisible(true);
        } else if (this._frame == this._interval * 32) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            this.setupDataHP(digimon.getHealthPoints(), digimon.getFullHealthPoints());
            this._sounds.playSound(SoundConfig._healthInc);
            this._healthBarFull.setVisible(true);
            this._healthBar.setVisible(true);
        } else if (this._frame == this._interval * 42) {
            this.resetScreen();
            this.endAnim();
        }
    }

    private void inheriting() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._opponent.setVisible(false);
            this._character.setLocX(this._mainDisplay.getWidth() / this.getScale() - this._character.getSizeX() / this.getScale() - 3);
            this._character.setLocY(63 - this._yPad);
            this._character.drawNumMirror(0, false);
            this._itemLabel.drawNumMirror(0, false);
            this._itemLabel.setLocX(this._character.getLocX() / this.getScale() - this._itemLabel.getSizeX() / this.getScale());
            this._itemLabel.setLocY(-this._itemLabel.getSizeY() / this.getScale());
        } else if (this._frame >= this._interval * 1 && this._frame <= this._interval * 10) {
            this._itemLabel.moveDown(1);
        } else if (this._frame == this._interval * 11) {
            this._sounds.playSound(SoundConfig._inheritChipShrink);
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 27, this._itemLabel.getSizeY() / this.getScale() - 24);
            this._itemLabel.moveDown(12);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 4, this._itemLabel.getSizeY() / this.getScale() - 4);
            this._itemLabel.moveDown(2);
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * 13) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 4, this._itemLabel.getSizeY() / this.getScale() - 4);
            this._itemLabel.moveDown(2);
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * 14) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 4, this._itemLabel.getSizeY() / this.getScale() - 4);
            this._itemLabel.moveDown(2);
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * 15) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 4, this._itemLabel.getSizeY() / this.getScale() - 5);
            this._itemLabel.moveDown(2);
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * 16) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 5, this._itemLabel.getSizeY() / this.getScale() - 4);
            this._itemLabel.moveDown(2);
            this._itemLabel.moveRight(2);
        } else if (this._frame == this._interval * 17) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            int index = 0;
            try {
                index = Integer.parseInt(this._itemType.getDetails());
            }
            catch (NumberFormatException numberFormatException) {
                // empty catch block
            }
            EvolutionInfo inherit = digimon.getEvolution().getDigimon(index);
            this.setOppSprites(this.getOppSet(inherit.getNewStage(), inherit.getNewSpriteSet(), inherit.getNewSpriteNum()));
            this._opponent.setSize(0, 0);
            this._opponent.setLoc(this._itemLabel.getLocX() / this.getScale() + 1, this._itemLabel.getLocY() / this.getScale() - 4);
            this._opponent.drawNumMirror(6, true);
            this._opponent.setVisible(true);
            this._itemLabel.setVisible(false);
        } else if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._inheritParentGrow);
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() + 12, this._opponent.getSizeY() / this.getScale() + 12);
            this._opponent.moveUp(4);
            this._opponent.moveLeft(4);
        } else if (this._frame == this._interval * 19) {
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() + 12, this._opponent.getSizeY() / this.getScale() + 12);
            this._opponent.moveUp(4);
            this._opponent.moveLeft(4);
        } else if (this._frame == this._interval * 20) {
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() + 12, this._opponent.getSizeY() / this.getScale() + 12);
            this._opponent.moveUp(4);
            this._opponent.moveLeft(4);
        } else if (this._frame == this._interval * 21) {
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() + 12, this._opponent.getSizeY() / this.getScale() + 12);
            this._opponent.moveUp(4);
            this._opponent.moveLeft(4);
        } else if (this._frame == this._interval * 24) {
            this._opponent.drawNumMirror(1, true);
        } else if (this._frame == this._interval * 27) {
            this._opponent.drawNumMirror(6, true);
        } else if (this._frame == this._interval * 30) {
            this._opponent.drawNumMirror(1, true);
        } else if (this._frame == this._interval * 33) {
            this._opponent.drawNumMirror(6, true);
        } else if (this._frame == this._interval * 37) {
            this._sounds.playSound(SoundConfig._inheritParentShrink);
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() - 12, this._opponent.getSizeY() / this.getScale() - 12);
            this._opponent.moveDown(4);
            this._opponent.moveRight(4);
        } else if (this._frame == this._interval * 38) {
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() - 12, this._opponent.getSizeY() / this.getScale() - 12);
            this._opponent.moveDown(4);
            this._opponent.moveRight(4);
        } else if (this._frame == this._interval * 39) {
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() - 12, this._opponent.getSizeY() / this.getScale() - 12);
            this._opponent.moveDown(4);
            this._opponent.moveRight(4);
        } else if (this._frame == this._interval * 40) {
            this._opponent.setSize(this._opponent.getSizeX() / this.getScale() - 12, this._opponent.getSizeY() / this.getScale() - 12);
            this._opponent.moveDown(4);
            this._opponent.moveRight(4);
        } else if (this._frame == this._interval * 42) {
            this._itemLabel.setVisible(true);
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 6, this._itemLabel.getSizeY() / this.getScale() + 3);
            this._itemLabel.moveUp(2);
            this._itemLabel.moveLeft(2);
        } else if (this._frame == this._interval * 44) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 1, this._itemLabel.getSizeY() / this.getScale() + 1);
            this._sounds.playSound(SoundConfig._inheritMove);
            this._itemLabel.moveRight(4);
        } else if (this._frame == this._interval * 46) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 1, this._itemLabel.getSizeY() / this.getScale() - 1);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() - 1);
        } else if (this._frame == this._interval * 48) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 1, this._itemLabel.getSizeY() / this.getScale() + 1);
            this._sounds.playSound(SoundConfig._inheritMove);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() + 2);
        } else if (this._frame == this._interval * 50) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 1, this._itemLabel.getSizeY() / this.getScale() - 1);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() - 2);
        } else if (this._frame == this._interval * 52) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 1, this._itemLabel.getSizeY() / this.getScale() + 1);
            this._sounds.playSound(SoundConfig._inheritMove);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() + 2);
        } else if (this._frame == this._interval * 54) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 1, this._itemLabel.getSizeY() / this.getScale() - 1);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() - 2);
        } else if (this._frame == this._interval * 56) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 1, this._itemLabel.getSizeY() / this.getScale() + 1);
            this._sounds.playSound(SoundConfig._inheritMove);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() + 2);
        } else if (this._frame == this._interval * 58) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 1, this._itemLabel.getSizeY() / this.getScale() - 1);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() - 2);
        } else if (this._frame == this._interval * 60) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 1, this._itemLabel.getSizeY() / this.getScale() + 1);
            this._sounds.playSound(SoundConfig._inheritMove);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() + 2);
        } else if (this._frame == this._interval * 62) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() - 1, this._itemLabel.getSizeY() / this.getScale() - 1);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() - 2);
        } else if (this._frame == this._interval * 64) {
            this._itemLabel.setSize(this._itemLabel.getSizeX() / this.getScale() + 1, this._itemLabel.getSizeY() / this.getScale() + 1);
            this._sounds.playSound(SoundConfig._inheritMove);
            this._itemLabel.moveRight(4);
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() + 2);
        } else if (this._frame == this._interval * 65) {
            this._sounds.playSound(SoundConfig._inheritCollide);
            this._itemLabel.setVisible(false);
            this._roomEffect.setAltIcon("evol");
            this._roomEffect.setVisible(true);
        } else if (this._frame == this._interval * 69) {
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * 71) {
            this._roomEffect.setAltIcon("evol");
            this._character.setVisible(false);
            this._opponent.setSize(48, 48);
            this._opponent.setLoc(this._character.getLocX() / this.getScale(), this._character.getLocY() / this.getScale());
            this._opponent.drawNumMirror(6, false);
        } else if (this._frame == this._interval * 75) {
            this._sounds.playSound(SoundConfig._inheritCollide);
            this._opponent.setVisible(false);
            this._character.setVisible(true);
            this._roomEffect.setAltIcon("lightsOff");
        } else if (this._frame == this._interval * 77) {
            this._roomEffect.setAltIcon("evol");
        } else if (this._frame == this._interval * 83) {
            this._roomEffect.setVisible(false);
        } else if (this._frame == this._interval * 89) {
            this._itemLabel.setSize(48, 48);
            this.endAnim();
        }
        if (this._frame % (this._interval * 6) == 0) {
            if (this._character.getSpriteNum() == 0) {
                this._character.drawNumMirror(1, false);
            } else {
                this._character.drawNumMirror(0, false);
            }
        }
    }

    private void cycleItemFrames(int rate, Enum.State endState) {
        if (this._frame <= this._interval * 0) {
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(81 - this._xPad);
            this._itemLabel.setLoc(3, 62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._frame = 0;
        } else if (this._frame == this._interval * rate) {
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 2)) {
            this._itemLabel.drawNumMirror(3, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 3)) {
            this._itemLabel.drawNumMirror(4, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 4)) {
            this._itemLabel.drawNumMirror(5, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 5)) {
            this._itemLabel.drawNumMirror(6, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 6)) {
            this._itemLabel.drawNumMirror(7, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 7)) {
            this._itemLabel.drawNumMirror(8, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * (rate * 8)) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)endState)) {
                this._frame = -7;
                this._currentAnim = endState;
            } else {
                this.endAnim();
            }
        }
    }

    private void studying() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(81 - this._xPad);
            this._itemLabel.setLoc(3, 62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
        } else if (this._frame == this._interval * 3) {
            this._sounds.playSound(SoundConfig._studyStart);
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._itemLabel.drawNumMirror(3, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 9) {
            this._itemLabel.drawNumMirror(4, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.drawNumMirror(5, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 17) {
            this._sounds.playSound(SoundConfig._studyProgress);
            this._itemLabel.drawNumMirror(6, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 22) {
            this._sounds.playSound(SoundConfig._studyProgress);
            this._itemLabel.drawNumMirror(7, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 27) {
            this._sounds.playSound(SoundConfig._studyProgress);
            this._itemLabel.drawNumMirror(8, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 32) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    private void poopToilet(boolean flush) {
        if (this._frame == this._interval * 3) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 6) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 9) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 12) {
            this._character.moveRight(3);
        } else if (this._frame == this._interval * 15) {
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 18) {
            this._character.moveRight(3);
            byte f = this._controller.getModel().getDigimon().poop(true);
            this.playPoopSound(f);
            this._character.drawNum(5);
        } else if (this._frame == this._interval * 28) {
            this._character.drawNum(1);
            if (flush) {
                this._sounds.playSound(SoundConfig._wash);
            } else {
                this._frame = this._interval * 31;
            }
        } else if (this._frame >= this._interval * 37) {
            this._controller.getModel().getDigimon().toiletTrain();
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    private void portToilet() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._itemLabel.setLoc(this._mainDisplay.getWidth() / this.getScale() / 2 - this._itemLabel.getWidth() / this.getScale() / 2, this._mainDisplay.getHeight() / this.getScale() - this._itemLabel.getHeight() / this.getScale());
            this._character.setLoc(this._itemLabel.getX() / this.getScale() + 9, this._mainDisplay.getHeight() / this.getScale() - 9 - this._character.getHeight() / this.getScale());
            this._itemLabel.drawNum(1);
            this._character.drawNumMirror(4, false);
        } else {
            this.poopToilet(false);
        }
    }

    private void selfPoopToilet(int item) {
        if (this._frame <= 0) {
            PhysicalState digimon = this._controller.getModel().getDigimon();
            String[] s = Utility.getCSVRecord(Utility.getInputStream(digimon.getModFolder(), digimon.getModelFolder(), "items.csv"), item);
            s[9] = "0";
            s[30] = "Idling";
            s[69] = "true";
            s[65] = "false";
            this._itemType = new Item(s);
            digimon.getItems().get(item).decQuantity();
            digimon.useItem(this._itemType);
        }
    }

    private void selfToilet() {
        this.selfPoopToilet(82);
        this.toilet();
    }

    private void selfPortToilet() {
        this.selfPoopToilet(83);
        this.portToilet();
    }

    private void toilet() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._itemLabel.setLoc(this._mainDisplay.getWidth() / this.getScale() - this._itemLabel.getWidth() / this.getScale(), this._mainDisplay.getHeight() / this.getScale() - this._itemLabel.getHeight() / this.getScale());
            this._character.setLoc(this._itemLabel.getX() / this.getScale(), this._mainDisplay.getHeight() / this.getScale() - 12 - this._character.getHeight() / this.getScale());
            this._itemLabel.drawNum(1);
            this._character.drawNumMirror(4, false);
        } else {
            this.poopToilet(true);
        }
    }

    private void interactXylophone() {
        int rate = 6;
        int interval = rate * this._interval;
        if (this._frame % interval == 0 && this._frame != interval * 8 && this._frame != interval * 5 && this._frame != interval * 4) {
            this._sounds.playSound(SoundConfig._xylophone);
        } else if (this._frame == interval * 4 || this._frame == interval * 5) {
            this._sounds.playSound(SoundConfig._xylophone);
            this._sounds.playSound(SoundConfig._xylophone2);
        }
        this.cycleItemFrames(rate, Enum.State.Cheering);
    }

    private void interactTelevision() {
        int rate = 6;
        int interval = rate * this._interval;
        if (this._frame == interval * 1 || this._frame == interval * 2 || this._frame == interval * 7) {
            this._sounds.playSound(SoundConfig._tvStatic);
        } else if (this._frame == interval * 3 || this._frame == interval * 4 || this._frame == interval * 5 || this._frame == interval * 6) {
            this._sounds.playSound(SoundConfig._monitorBeep);
        }
        this.cycleItemFrames(rate, Enum.State.Cheering);
    }

    private void interactComputer() {
        int rate = 6;
        int interval = rate * this._interval;
        if (this._frame == interval * 1 || this._frame == interval * 3 || this._frame == interval * 2 || this._frame == interval * 7) {
            this._sounds.playSound(SoundConfig._monitorBeep);
        } else if (this._frame == interval * 4 || this._frame == interval * 5) {
            this._sounds.playSound(SoundConfig._computerFlash);
        } else if (this._frame == interval * 6) {
            this._sounds.playSound(SoundConfig._tvStatic);
        }
        this.cycleItemFrames(rate, Enum.State.Cheering);
    }

    private void interactToyOven() {
        int rate = 6;
        int interval = rate * this._interval;
        if (this._frame == interval) {
            this._sounds.playSound(SoundConfig._pour);
        } else if (this._frame == interval * 3 || this._frame == interval * 4) {
            this._sounds.playSound(SoundConfig._ovenSet);
        } else if (this._frame == interval * 6) {
            this._sounds.playSound(SoundConfig._ovenFinish);
        }
        this.cycleItemFrames(rate, Enum.State.Cheering);
    }

    private void interactingSound(Enum.State endState) {
        int rate = 6;
        if (this._frame % (rate * this._interval) == 0 && this._frame != rate * this._interval * 1 && this._frame != rate * this._interval * 8) {
            this._sounds.playSound(SoundConfig._interact);
        }
        this.cycleItemFrames(rate, endState);
    }

    private void recover() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this._menuButton.setVisible(true);
            this.setItemSet();
            this._itemLabel.setVisible(true);
            this._itemLabel.setLocX(31 - this._xPad);
            this._itemLabel.setLocY(-this._itemLabel.getSizeY() / this.getScale());
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.setVisible(true);
            this._character.setLocX(this._itemLabel.getLocX() / this.getScale() + this._itemLabel.getSizeX() / this.getScale() + 3);
        } else if (this._itemLabel.getLocY() / this.getScale() < this._mainDisplay.getHeight() / this.getScale() - this._itemLabel.getSizeY() / this.getScale() - 5 && this._frame % 5 == 0) {
            this._itemLabel.setLocY(this._itemLabel.getLocY() / this.getScale() + 5);
        } else if (this._frame == this._interval * 10) {
            this._character.drawNumMirror(8, false);
        } else if (this._frame == this._interval * 14) {
            this._sounds.playSound(SoundConfig._adventureLifeRecover);
            this._character.drawNumMirror(7, false);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 18) {
            this._character.drawNumMirror(8, false);
            if (this._controller.getModel().getDigimon().getBaseWeight() >= 40) {
                this._frame = this._interval * 26;
            }
        } else if (this._frame == this._interval * 22) {
            this._sounds.playSound(SoundConfig._adventureLifeRecover);
            this._character.drawNumMirror(7, false);
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 26) {
            this._character.drawNumMirror(8, false);
        } else if (this._frame == this._interval * 30) {
            this._sounds.playSound(SoundConfig._adventureLifeRecover);
            this._character.drawNumMirror(7, false);
            this._itemLabel.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 34) {
            this._character.drawNumMirror(8, false);
        } else if (this._frame == this._interval * 38) {
            this._sounds.playSound(SoundConfig._adventureLifeRecover);
            this._character.drawNumMirror(7, false);
            this._itemLabel.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 42) {
            this._itemLabel.setVisible(false);
            this._itemLabel.setLocX(-100);
            this._menuButton.setVisible(false);
            this.endAnim();
            this._controller.getModel().getDigimon().setCurrentState(Enum.State.LifeInc);
        }
    }

    private void playing(Enum.State endState) {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(81 - this._xPad);
            this._itemLabel.setLoc(3, 62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._playingInteract);
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.drawNumMirror(3, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._playingInteract);
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 24) {
            this._itemLabel.drawNumMirror(3, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 30) {
            this._sounds.playSound(SoundConfig._playingInteract);
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 36) {
            this._itemLabel.setVisible(false);
            this.setSpriteCharDefault();
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)endState)) {
                this._frame = -7;
                this._currentAnim = endState;
            } else {
                this.endAnim();
            }
        }
    }

    private void angrySurprise(Enum.State endState) {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(81 - this._xPad);
            this._itemLabel.setLoc(3, 62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._interact);
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 12) {
            this._sounds.playSound(SoundConfig._interact);
            this._itemLabel.drawNumMirror(3, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._interact);
            this._itemLabel.drawNumMirror(4, false);
            this._character.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 24) {
            this._sounds.playSound(SoundConfig._interact);
            this._itemLabel.drawNumMirror(5, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 30) {
            this._sounds.playSound(SoundConfig._refuse);
            this._itemLabel.drawNumMirror(6, false);
            this._character.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 36) {
            this._itemLabel.drawNumMirror(7, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 42) {
            this._sounds.playSound(SoundConfig._refuse);
            this._itemLabel.drawNumMirror(8, false);
            this._character.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 48) {
            this._itemLabel.setVisible(false);
            this.setSpriteCharDefault();
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)endState)) {
                this._frame = -7;
                this._currentAnim = endState;
            } else {
                this.endAnim();
            }
        }
    }

    private void lifting() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(81 - this._xPad);
            this._itemLabel.setLoc(3, 62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._lifting);
            this._itemLabel.setLocY(46 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(8, false);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.setLocY(62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._lifting);
            this._itemLabel.setLocY(46 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(8, false);
        } else if (this._frame == this._interval * 24) {
            this._itemLabel.setLocY(62 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 30) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    private void showering() {
        int loc = (71 - this._xPad) * this.getScale();
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this.setSpriteCharDefault();
            this._character.setLocX(71 - this._xPad);
            this._itemLabel.setLoc(-36 + this._character.getLocX() / this.getScale(), this._character.getLocY() / this.getScale());
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(9, false);
        } else if (this._frame == this._interval * 4) {
            this._sounds.playSound(SoundConfig._showerOn);
            this._itemLabel.drawNumMirror(2, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 8) {
            this._sounds.playSound(SoundConfig._showerWash);
            this._itemLabel.drawNumMirror(3, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 12) {
            this._sounds.playSound(SoundConfig._showerWash);
            this._itemLabel.drawNumMirror(4, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 16) {
            this._sounds.playSound(SoundConfig._showerWash);
            this._itemLabel.drawNumMirror(5, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 20) {
            this._sounds.playSound(SoundConfig._showerWash);
            this._itemLabel.drawNumMirror(6, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 24) {
            this._sounds.playSound(SoundConfig._showerWash);
            this._itemLabel.drawNumMirror(7, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 28) {
            this._itemLabel.drawNumMirror(8, false);
            this.shakeObj(this._character, loc);
        } else if (this._frame == this._interval * 36) {
            this._sounds.playSound(SoundConfig._showerEnd);
            this._character.moveRight(1);
            this._character.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 40) {
            this._character.drawNumMirror(6, false);
        } else if (this._frame == this._interval * 44) {
            this._character.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 48) {
            this._character.drawNumMirror(6, false);
        } else if (this._frame == this._interval * 52) {
            this._character.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 56) {
            this._itemLabel.setVisible(false);
            this.setSpriteCharDefault();
            this.endAnim();
        }
    }

    private void setCropSprite(Icon i, int rotations, int pad) {
        Icon r = ViewUtil.getRotatedIcon(rotations, i);
        ImageIcon crop = new ImageIcon(ViewUtil.trimImage(ViewUtil.createBuffImage(r), 1.0, 0.67, 3 * this.getScale(), 12 * this.getScale(), 21 * this.getScale()));
        this._character.setLocY(this._itemLabel.getLocY() / this.getScale() + pad - crop.getIconHeight() / this.getScale());
        this._character.setIcon(crop);
    }

    private void futonSleep(EvolutionInfo e, boolean nap) {
        int pad = 24;
        if (this._frame <= this._interval * 0) {
            this._frame = 11 * this._interval;
            this._itemType = this._controller.getModel().getDigimon().getItemByID(81);
            this.setItemSet();
            this._character.setVerticalAlignment(1);
            this.setSpriteCharDefault();
            this.adjustCharacterForFilth();
            this._itemLabel.setLoc(this._character.getLocX() / this.getScale(), this._character.getLocY() / this.getScale() + 3);
            this.setCropSprite(this._character.getSpriteSheet()[2], e.getSpriteRotations(), pad);
            int loc = ViewUtil.centerObj(this._itemLabel, this._character.getIcon(), this.getScale(), 3)[0];
            this._character.setLocX(loc);
            String s = nap ? "napLights" : "sleepLights";
            this._emotionLabel.setAltIcon(s);
            this._emotionLabel.setVisible(true);
            this._itemLabel.drawNumMirror(1, false);
            this._character.setVisible(true);
        } else if (this._frame == this._interval * 11) {
            String s = nap ? "napLights" : "sleepLights";
            this._emotionLabel.setAltIcon(s);
            this.setCropSprite(this._character.getSpriteSheet()[2], e.getSpriteRotations(), pad);
        } else if (this._frame >= this._interval * 21) {
            String s = nap ? "napLights2" : "sleepLights2";
            this._emotionLabel.setAltIcon(s);
            this.setCropSprite(this._character.getSpriteSheet()[3], e.getSpriteRotations(), pad);
            this._frame = 1 * this._interval;
        }
    }

    private void bathing() {
        int pad = 27;
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setVerticalAlignment(1);
            this.setSpriteCharDefault();
            this._itemLabel.setLoc(this._character.getLocX() / this.getScale(), this._character.getLocY() / this.getScale() + 3);
            this._itemLabel.drawNumMirror(1, false);
            this.setCropSprite(this._character.getSpriteSheet()[9], 0, pad);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._bathing);
            this._itemLabel.drawNumMirror(2, false);
            this.setCropSprite(this._character.getSpriteSheet()[10], 0, pad);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.drawNumMirror(1, false);
            this.setCropSprite(this._character.getSpriteSheet()[9], 0, pad);
        } else if (this._frame == this._interval * 18) {
            this._sounds.playSound(SoundConfig._bathing);
            this._itemLabel.drawNumMirror(2, false);
            this.setCropSprite(this._character.getSpriteSheet()[10], 0, pad);
        } else if (this._frame == this._interval * 24) {
            this._itemLabel.drawNumMirror(1, false);
            this.setCropSprite(this._character.getSpriteSheet()[9], 0, pad);
        } else if (this._frame == this._interval * 30) {
            this._sounds.playSound(SoundConfig._bathing);
            this._itemLabel.drawNumMirror(2, false);
            this.setCropSprite(this._character.getSpriteSheet()[10], 0, pad);
        } else if (this._frame == this._interval * 36) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    private void riding() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(83 - this._xPad);
            this._itemLabel.setLoc(65 - this._xPad, 65 - this._yPad);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._sounds.playSound(SoundConfig._rideJump);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveUp(3);
        } else if (this._frame == this._interval * 7) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveUp(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 8) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveUp(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 9) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveUp(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 10) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 11) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveDown(3);
            this._character.moveLeft(3);
        } else if (this._frame == this._interval * 13) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(0, false);
            this._character.moveDown(3);
        } else if (this._frame == this._interval * 14) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 15) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 16) {
            this._itemLabel.drawNumMirror(2, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 17) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 18) {
            this._itemLabel.drawNumMirror(2, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 19) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 20) {
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(5, false);
            this._sounds.playSound(SoundConfig._happy);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 21) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 22) {
            this._itemLabel.drawNumMirror(2, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 23) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 24) {
            this._itemLabel.drawNumMirror(2, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 25) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 26) {
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 27) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 28) {
            this._itemLabel.drawNumMirror(2, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 29) {
            this._itemLabel.drawNumMirror(1, false);
            this._itemLabel.moveLeft(6);
            this._character.moveLeft(6);
        } else if (this._frame == this._interval * 35) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    private void jumping() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this.setSpriteCharDefault();
            this._itemLabel.setLoc(this._character.getLocX() / this.getScale(), this._character.getLocY() / this.getScale() + 6);
            this._character.setLocY(this._character.getLocY() - 18);
            this._itemLabel.drawNumMirror(2, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(5, false);
            this._sounds.playSound(SoundConfig._happy);
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 7) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 8) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 9) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 10) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 11) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 12) {
            this._character.drawNumMirror(1, false);
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 13) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 14) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 15) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 16) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 17) {
            this._itemLabel.drawNumMirror(2, false);
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 20) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(5, false);
            this._sounds.playSound(SoundConfig._happy);
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 21) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 22) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 23) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 24) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 25) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 26) {
            this._character.drawNumMirror(1, false);
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 27) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 28) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 29) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 30) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 31) {
            this._itemLabel.drawNumMirror(2, false);
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 34) {
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(5, false);
            this._sounds.playSound(SoundConfig._happy);
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 35) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 36) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 37) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 38) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 39) {
            this._character.moveUp(6);
        } else if (this._frame == this._interval * 40) {
            this._character.drawNumMirror(1, false);
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 41) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 42) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 43) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 44) {
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 45) {
            this._itemLabel.drawNumMirror(2, false);
            this._character.moveDown(6);
        } else if (this._frame == this._interval * 48) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    private void bouncing() {
        if (this._frame <= this._interval * 0) {
            this._frame = 0;
            this.resetScreen();
            this.setItemSet();
            this._character.setVisible(true);
            this._itemLabel.setVisible(true);
            this._character.setLocX(83 - this._xPad);
            this._itemLabel.setLoc(35 - this._xPad, 48 - this._yPad - 48);
            this._itemLabel.drawNumMirror(1, false);
            this._character.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 6) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 7) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 8) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 9) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 10) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 11) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 12) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 13) {
            this._itemLabel.moveDown(6);
            this._itemLabel.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 14) {
            this._itemLabel.moveUp(3);
            this._itemLabel.moveLeft(6);
            this._sounds.playSound(SoundConfig._hitBall);
            this._itemLabel.drawNumMirror(5, false);
            this._character.drawNumMirror(5, false);
        } else if (this._frame == this._interval * 15) {
            this._itemLabel.moveUp(3);
            this._itemLabel.moveLeft(6);
            this._itemLabel.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 16) {
            this._itemLabel.moveUp(3);
            this._itemLabel.moveLeft(6);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 17) {
            this._itemLabel.moveUp(3);
            this._itemLabel.moveLeft(6);
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 18) {
            this._itemLabel.moveUp(3);
            this._itemLabel.moveLeft(6);
            this._itemLabel.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 19) {
            this._itemLabel.moveLeft(6);
            this._itemLabel.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 20) {
            this._itemLabel.moveLeft(6);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 21) {
            this._itemLabel.moveDown(3);
            this._itemLabel.moveLeft(3);
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 22) {
            this._itemLabel.moveDown(3);
            this._itemLabel.moveLeft(3);
            this._itemLabel.drawNumMirror(4, false);
        } else if (this._frame == this._interval * 23) {
            this._itemLabel.moveDown(3);
            this._itemLabel.moveLeft(3);
            this._itemLabel.drawNumMirror(1, false);
        } else if (this._frame == this._interval * 24) {
            this._itemLabel.moveDown(3);
            this._itemLabel.moveLeft(3);
            this._itemLabel.drawNumMirror(2, false);
        } else if (this._frame == this._interval * 25) {
            this._itemLabel.moveDown(3);
            this._itemLabel.moveLeft(3);
            this._itemLabel.drawNumMirror(3, false);
        } else if (this._frame == this._interval * 31) {
            if (!this._controller.getModel().getDigimon().getAnimQueue().contains((Object)Enum.State.Cheering)) {
                this._frame = 0;
                this._currentAnim = Enum.State.Cheering;
                this.cheer(true, SoundConfig._happy, true);
            } else {
                this.endAnim();
            }
        }
    }

    public void setSpriteCharDefault() {
        this.setSpriteCharDefault(-1);
    }

    private void adjustEmotionLabel() {
        int x = 3 + this._character.getSizeX() + this._character.getLocX();
        this._emotionLabel.setLocX(x / this.getScale());
    }

    private void setSpriteCharDefaultY() {
        this._character.setLocY(63 - this._yPad);
    }

    private void setSpriteCharDefault(int spriteNum) {
        this._character.setLocX(55 - this._xPad);
        this.setSpriteCharDefaultY();
        this._character.setSizeX(48);
        this._character.setSizeY(48);
        this.adjustEmotionLabel();
        if (spriteNum > -1) {
            this._character.drawNumMirror(spriteNum, false);
        }
    }

    private int getSpriteNum() {
        return 0;
    }

    private void showLoading() {
    }

    private void drawAttribute(Enum.Attribute attribute) {
        this._typeLabel.setLocX(12);
        this._typeLabel.setVisible(true);
        this._attribute.setLocX(this._typeLabel.getLocX() / this.getScale() + this._typeLabel.getSizeX() / this.getScale() + 4);
        this._attribute.setLocY(this._typeLabel.getLocY() / this.getScale() - this._attribute.getSizeY() / this.getScale() / 6);
        this._rightButton.setLocX(this._attribute.getLocX() / this.getScale() + this._attribute.getSizeX() / this.getScale());
        this._rightButton.setLocY(this._typeLabel.getLocY() / this.getScale() - 4);
        this._rightButton.setVisible(true);
        this.checkAttribute(attribute);
        this._attribute.setVisible(true);
    }

    private void checkAttribute(Enum.Attribute attribute) {
        switch (attribute) {
            case None: {
                this._attribute.setAltIcon("null");
                this._rightButton.moveRight(3);
                break;
            }
            case Vaccine: {
                this._attribute.setIcon(this._vaccineAttack.getIcon());
                break;
            }
            case Data: {
                this._attribute.setIcon(this._dataAttack.getIcon());
                break;
            }
            case Virus: {
                this._attribute.setIcon(this._virusAttack.getIcon());
            }
        }
    }

    private void drawType() {
        this._typeLabel.setLocY(this._agePanel.getY() / this.getScale() + this._agePanel.getHeight() / this.getScale() + 1);
        PhysicalState digimon = this._controller.getModel().getDigimon();
        switch (this._typeLabel.getText()) {
            case "Elmnt.": {
                this.drawElement(digimon.getElement());
                break;
            }
            case "Field": {
                this.drawField(digimon.getField());
                break;
            }
            case "Attrb.": {
                this.drawAttribute(digimon.getAttribute());
            }
        }
    }

    public void cycleType() {
        switch (this._typeLabel.getText()) {
            case "Elmnt.": {
                this._elementLabel.setVisible(false);
                this._typeLabel.setText("Field");
                break;
            }
            case "Field": {
                this._fieldLabel.setVisible(false);
                this._typeLabel.setText("Attrb.");
                break;
            }
            case "Attrb.": {
                this._attribute.setVisible(false);
                this._typeLabel.setText("Elmnt.");
            }
        }
        this.drawType();
    }

    private void drawElement(Enum.Element element) {
        this._typeLabel.setLocX(element == Enum.Element.Metal ? 3 : 9);
        this._typeLabel.setVisible(true);
        this._elementLabel.setVisible(true);
        this._elementLabel.setLocX(this._typeLabel.getLocX() / this.getScale() / 2 + this._typeLabel.getSizeX() / this.getScale() / 2 + 1);
        this._elementLabel.setLocY(this._typeLabel.getLocY() / this.getScale() / 2 - this._elementLabel.getSizeY() / this.getScale() / 2 / 4);
        this.changeElementIcon(element);
        this._rightButton.setLocX(this._elementLabel.getLocX() / this.getScale() + this._elementLabel.getSizeX() / this.getScale() + 3);
        this._rightButton.setLocY(this._typeLabel.getLocY() / this.getScale() - 3);
        this._rightButton.setVisible(true);
    }

    private void changeElementIcon(Enum.Element element) {
        this._elementLabel.setSizeX(15);
        switch (element) {
            case None: {
                this._elementLabel.setAltIcon("null");
                this._elementLabel.setSizeX(12);
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
                break;
            }
        }
    }

    private void drawField(Enum.Field field) {
        this._typeLabel.setLocX(13);
        this._typeLabel.setVisible(true);
        this._fieldLabel.setVisible(true);
        this._fieldLabel.setLocX(this._typeLabel.getLocX() / this.getScale() / 2 + this._typeLabel.getSizeX() / this.getScale() / 2 - 2);
        this._fieldLabel.setLocY(this._typeLabel.getLocY() / this.getScale() / 2 - this._fieldLabel.getSizeY() / this.getScale() / 2 / 4);
        this._rightButton.setLocX(this._fieldLabel.getLocX() / this.getScale() + this._fieldLabel.getSizeX() / this.getScale() + 3);
        this._rightButton.setLocY(this._typeLabel.getLocY() / this.getScale() - 4);
        this._rightButton.setVisible(true);
        this.checkField(field);
        this._fieldLabel.setVisible(true);
    }

    private void checkField(Enum.Field field) {
        switch (field) {
            case DragonsRoar: {
                this._fieldLabel.drawNumMirror(2, false);
                break;
            }
            case DeepSaver: {
                this._fieldLabel.drawNumMirror(4, false);
                break;
            }
            case JungleTrooper: {
                this._fieldLabel.drawNumMirror(3, false);
                break;
            }
            case MetalEmpire: {
                this._fieldLabel.drawNumMirror(1, false);
                break;
            }
            case NatureSpirit: {
                this._fieldLabel.drawNumMirror(7, false);
                break;
            }
            case WindGuardian: {
                this._fieldLabel.drawNumMirror(6, false);
                break;
            }
            case NightmareSoldier: {
                this._fieldLabel.drawNumMirror(5, false);
                break;
            }
            case DarkArea: {
                this._fieldLabel.drawNumMirror(8, false);
                break;
            }
            case VirusBuster: {
                this._fieldLabel.drawNumMirror(0, false);
                break;
            }
            case None: {
                this._fieldLabel.drawNumMirror(9, false);
                break;
            }
        }
    }

    private void checkHealthTracker(int wins) {
        int i = wins / Config._perfectWinsLimit;
        double d = (double)wins / (double)Config._perfectWinsLimit;
        double a = (double)Math.round((d - (double)i) * 10.0) / 10.0;
        int frames = this._healthUp.getSpriteSheet().length - 1;
        double f = (double)frames * a;
        this._healthUp.setLocX(this._mainDisplay.getWidth() / this.getScale() / 2 - this._healthUp.getSizeX() / this.getScale() / 2);
        this._healthUp.setLocY(this._mainDisplay.getHeight() / this.getScale() / 2 - this._healthUp.getSizeY() / this.getScale() / 2);
        this._healthUp.drawNumMirror((int)f, false);
        this._healthUp.setVisible(true);
    }

    private void showHunger(PhysicalState digimon, int size, int x, int y) {
        byte hunger = digimon.getHunger();
        int newSize = size * (hunger > 4 ? 4 : (int)hunger);
        this._optionButton.setSize(17, 12);
        this._optionButton.setLoc(this._mainInteract.getWidth() / this.getScale() - this._optionButton.getSizeX() / this.getScale() - 3, 5);
        this._optionButton.setAltIcon("tNutrition");
        this._optionButton.setVisible(true);
        this._hungerLabel.setAltIcon("emptyHearts");
        this._fullHunger.setAltIcon("fullHearts");
        this._fullHunger.setSizeX(newSize);
        this._hungerLabel.setLoc(x, y);
        this._fullHunger.setLoc(x, y);
        this._fullHunger.setVisible(true);
        this._hungerLabel.setVisible(true);
    }

    private void showStrength(PhysicalState digimon, int size, int x, int y) {
        byte exercise = digimon.getExercise();
        int newSize = size * (exercise > 4 ? 4 : (int)exercise);
        this.showHearts(newSize, x, y);
    }

    private void showIncrementalHearts(double current, int x, int y) {
        int newSize = this.getIncrementalHeartSize(current, 4.0, 16.0);
        this.showHearts(newSize, x, y);
    }

    private int getIncrementalHeartSize(double current, double inc, double size) {
        double padding = (double)((int)current) * (0.25 * size) + Math.ceil(current) * (size * 0.125);
        return (int)(size * 0.625 * (current > inc ? inc : current) + padding);
    }

    private void showHearts(int size, int x, int y) {
        this._fullExercise.setAltIcon("fullHearts");
        this._exerciseLabel.setAltIcon("emptyHearts");
        this._exerciseLabel.setSize(62, 14);
        this._fullExercise.setSizeX(size);
        this._fullExercise.setLoc(x, y);
        this._exerciseLabel.setLoc(x, y);
        this._fullExercise.setVisible(true);
        this._exerciseLabel.setVisible(true);
    }

    private void checkSleep() {
        double proportion;
        int full = 7;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (digimon.getAsleep()) {
            double current = Math.floor((double)digimon.getAwakeLapse() / (double)digimon.getAwakeLimit() * (double)full);
            proportion = (double)full - current;
        } else {
            double current = (double)digimon.getSleepLapse() / (double)digimon.getSleepLimit();
            proportion = Math.floor(current * (double)full);
        }
        this._sleepLabel.drawNumMirror((int)proportion, false);
    }

    private void checkEnergy() {
        double energy = (double)this._controller.getModel().getDigimon().getEnergy() / (double)this._controller.getModel().getDigimon().getMaxEnergy();
        double fullSize = 96.0;
        this._energyBar.setSizeX((int)(fullSize * energy));
    }

    private void checkObedience() {
        int obedience = this._controller.getModel().getDigimon().getObedience();
        int fullSize = 41;
        double obediencePercent = (double)obedience / 100.0;
        if (obediencePercent > 1.0) {
            obediencePercent = 1.0;
        }
        int newSize = (int)Math.floor((double)fullSize * obediencePercent);
        int inc = 0;
        if (obedience < 50) {
            this._obedienceLabel.setAltIcon("obedienceBar");
        } else if (obedience >= 100) {
            this._obedienceLabel.setAltIcon("obedienceBarFull");
        } else {
            this._obedienceLabel.setAltIcon("obedienceBarHalf");
        }
        this._obedienceLabel.setLoc(this._moodLabel.getLocX() / this.getScale() + this._moodLabel.getWidth() / this.getScale() + 6, this._moodLabel.getLocY() / this.getScale() + this._obedienceLabel.getHeight() / 2 / this.getScale() - 1);
        this._obedienceFull.setSizeX(newSize);
        this._obedienceFull.setLoc(this._obedienceLabel.getLocX() / this.getScale() + 14 + inc, this._obedienceLabel.getLocY() / this.getScale() + 4);
    }

    private String checkPersonality() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        return digimon.getPersonality().toString();
    }

    private void setupFavFoodLabel(Enum.Food food) {
        int foodNum = ViewUtil.getFoodGroupNum(food);
        if (food != Enum.Food.None) {
            this._foodType = this._controller.getModel().getDigimon().getFoodByID(foodNum);
            this.setFoodSet();
            this._favFoodLabel.setIcon(this._foodLabel.getSpriteSheet()[0]);
        } else {
            this._favFoodLabel.setAltIcon("null");
        }
    }

    private void checkFavDisplay(Enum.Time time, Enum.Food food, Enum.Attribute attribute) {
        if (food != null) {
            this.setupFavFoodLabel(food);
        } else {
            this._favFoodLabel.setAltIcon("locked");
        }
        if (attribute != null) {
            switch (attribute) {
                case Data: {
                    this._favAttLabel.setIcon(ViewUtil.resizeImage(this._dataAttack.getIcon(), 2.0));
                    break;
                }
                case Virus: {
                    this._favAttLabel.setIcon(ViewUtil.resizeImage(this._virusAttack.getIcon(), 2.0));
                    break;
                }
                case Vaccine: {
                    this._favAttLabel.setIcon(ViewUtil.resizeImage(this._vaccineAttack.getIcon(), 2.0));
                    break;
                }
                case None: {
                    this._favAttLabel.setAltIcon("null");
                }
            }
        } else {
            this._favAttLabel.setAltIcon("locked");
        }
        if (time != null) {
            switch (time) {
                case Morning: {
                    this._favTimeLabel.setIcon(this._timeLabel.getAltSprites().get(2));
                    break;
                }
                case Noon: {
                    this._favTimeLabel.setIcon(this._timeLabel.getAltSprites().get(1));
                    break;
                }
                case Night: {
                    this._favTimeLabel.setIcon(this._timeLabel.getAltSprites().get(0));
                    break;
                }
                case None: {
                    this._favTimeLabel.setAltIcon("null");
                }
            }
        } else {
            this._favTimeLabel.setAltIcon("locked");
        }
        this._favFoodLabel.setVisible(true);
        this._favAttLabel.setVisible(true);
        this._favTimeLabel.setVisible(true);
    }

    private boolean isUnderage() {
        boolean isUnder = false;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        if (digimon.getGrowthStage() == Enum.Stage.Egg || digimon.getGrowthStage() == Enum.Stage.Fresh || digimon.getGrowthStage() == Enum.Stage.InTraining) {
            isUnder = true;
        }
        return isUnder;
    }

    @Override
    public void dispose() {
        this._back.removeAll();
        this._display.removeAll();
        this._mainDisplay.removeAll();
        this._shell.removeAll();
        this._overlay.removeAll();
        this._menuInteract.removeAll();
        this._mainInteract.removeAll();
        this._interact.removeAll();
        this._weather.stopWeather();
        this._weather = null;
        super.dispose();
    }

    private void displayMessage(String message, Enum.Menu currentMenu, Enum.Menu lastMenu, PhysicalState digimon, ViewSettings settings) {
        this._message = message;
        this.displayMessage(currentMenu, lastMenu, digimon, settings);
    }

    public void displayMessage(Enum.Menu currentMenu, Enum.Menu lastMenu, PhysicalState digimon, ViewSettings settings) {
        if (this._frame <= 0) {
            this.resetScreen();
            this._frame = 0;
            this._menuRect.setVisible(true);
            this._messageDisplay.setText(this._message);
            this._messageDisplay.setVisible(true);
        } else if (this._frame >= Config._messageDisplayTime * this._interval * this._controller.getModel().getTime().getFastMod()) {
            this._frame = -8 * this._interval;
            this._messageDisplay.setVisible(false);
            this._message = null;
            this.checkSystemMenus(currentMenu, lastMenu, digimon, settings);
        }
        ++this._frame;
    }

    private void checkTrophyNum() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        for (int trophy = 0; trophy < digimon.getTrophySchedule().length; ++trophy) {
            this._trophyInSchedule = trophy;
            if (!digimon.getTournament().checkTourneyClosed(digimon.getTournament().getTourneyTime(trophy), this._controller.getModel().getTime().getHours())) break;
        }
    }

    public void initStringPane(int limit) {
        if (this._stringPane != null) {
            this._interact.remove(this._stringPane);
        }
        this._stringPane = new JTextField();
        this._stringPane.setOpaque(false);
        this._stringPane.setEditable(true);
        if (limit > 0) {
            this._stringPane.setDocument(new JTextFieldLimit(limit));
        }
        this._stringPane.setText("");
        this._stringPane.setFont(this._bit.deriveFont((float)(28 * this.getScale())));
        this._stringPane.setForeground(Color.BLACK);
        this._stringPane.setBounds(24 * this.getScale(), 38 * this.getScale(), 127 * this.getScale(), 19 * this.getScale());
        this._stringPane.setBorder(BorderFactory.createEmptyBorder());
        this._interact.add(this._stringPane);
        this._stringPane.addActionListener(new ActionListener(){

            @Override
            public void actionPerformed(ActionEvent evt) {
                SpriteAnim.this._controller.onEnter();
            }
        });
        this._stringPane.addKeyListener(new KeyAdapter(){

            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == ViewConfig._textFieldEscapeKey) {
                    SpriteAnim.this._controller.requestViewFocus();
                    int i = SpriteAnim.this._keyboard.getCursorPosition();
                    SpriteAnim.this._keyboard.incCursor();
                    SpriteAnim.this._keyboard.moveCursor(i);
                } else if (ViewConfig._enableTextFieldKeyboardCursor) {
                    e.consume();
                }
            }
        });
        this._stringPane.setVisible(false);
    }

    private boolean isOverlap(int x, int width, SpriteObj second) {
        return x < second.getLocX() && x + width > second.getLocX() || x > second.getLocX() && x < second.getLocX() + second.getSizeX();
    }

    private void drawTowns(Zone zone) {
        int fullSize = 93 * this.getScale();
        int sectionWidth = 6 * this.getScale();
        double totalSections = 16.0;
        double maxLocation = zone.getTotalSteps();
        BufferedImage townLabel = new BufferedImage(this._townLabel.getSizeX(), this._townLabel.getSizeY(), 2);
        Graphics2D g2 = townLabel.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        for (Town t : zone.getTowns()) {
            Icon townIcon = ViewUtil.resizeImage(ViewUtil.getResource(this.MOD_FOLDER, this.RESOURCES_FOLDER, t.getSmallTownIcon()), (double)this.getScale());
            BufferedImage town = ViewUtil.createBuffImage(townIcon);
            double location = t.getBackgroundRange().getRange()[0];
            int currentSection = (int)(totalSections * (location / maxLocation));
            int newSize = currentSection * sectionWidth;
            int newLoc = this._zoneDetail.getLocX() + 3 * this.getScale() + (fullSize - newSize) - 7 * this.getScale() - town.getWidth() / 4;
            int y = this._townLabel.getSizeY() - town.getHeight() - this.getScale();
            if (zone.isTown() == null) {
                int padding = 0;
                if (this.isOverlap(newLoc, town.getWidth(), this._participants[0])) {
                    padding = 16 * this.getScale();
                }
                y -= padding;
            } else {
                this._participants[0].setVisible(false);
            }
            g2.drawImage(town, null, newLoc, y);
        }
        g2.dispose();
        this._townLabel.setIcon(new ImageIcon(townLabel));
    }

    private void drawBattleEndIcons(ImageIcon icon) {
        BufferedImage end = ViewUtil.createBuffImage(icon);
        BufferedImage full = new BufferedImage(this._roomEffect.getSizeX(), this._roomEffect.getSizeY(), 2);
        Graphics2D g2 = full.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        g2.drawImage(end, null, this._character.getLocX() - end.getWidth(), this._character.getLocY());
        g2.drawImage(end, null, this._character.getLocX() - end.getWidth(), this._character.getLocY() + end.getHeight());
        g2.drawImage(end, null, this._character.getLocX() + this._character.getWidth(), this._character.getLocY());
        g2.drawImage(end, null, this._character.getLocX() + this._character.getWidth(), this._character.getLocY() + end.getHeight());
        g2.dispose();
        this._roomEffect.setIcon(new ImageIcon(full));
    }

    private void drawSaleAlerts(Enum.Menu menu) {
        SpriteObj[] so;
        ImageIcon i = ViewUtil.getResourceAsImageIcon(this.MOD_FOLDER, this.RESOURCES_FOLDER, "attention.png");
        BufferedImage alert = ViewUtil.createBuffImage(ViewUtil.resizeImage(i, (double)this.getScale() / 3.0));
        BufferedImage alertList = new BufferedImage(this._roomEffect.getSizeX(), this._roomEffect.getSizeY(), 2);
        Graphics2D g2 = alertList.createGraphics();
        Color oldColor = g2.getColor();
        g2.fillRect(0, 0, 0, 0);
        g2.setColor(oldColor);
        for (SpriteObj o : so = new SpriteObj[]{this._meatButton, this._fishButton, this._vegButton, this._fruitButton}) {
            ShopConsumable sc = this.assignConsumableTypes(o, menu);
            if (sc == null || !sc.isSale()) continue;
            g2.drawImage(alert, null, o.getX() + o.getWidth() + 0 * this.getScale(), o.getY() + 3 * this.getScale());
        }
        g2.dispose();
        this._roomEffect.setIcon(new ImageIcon(alertList));
        this._roomEffect.setVisible(true);
    }

    private void doubleAttack(SpriteObj attackSprite) {
        if (attackSprite.getIcon() != null) {
            BufferedImage attack = ViewUtil.createBuffImage(attackSprite.getIcon());
            BufferedImage newAttack = new BufferedImage(attack.getWidth(), attack.getHeight() * 2, 2);
            attackSprite.setSizeY(48);
            Graphics2D g2 = newAttack.createGraphics();
            Color oldColor = g2.getColor();
            g2.fillRect(0, 0, 0, 0);
            g2.setColor(oldColor);
            g2.drawImage(attack, null, 0, 0);
            g2.drawImage(attack, null, 0, attack.getHeight());
            g2.dispose();
            attackSprite.setIcon(new ImageIcon(newAttack));
        }
    }

    private MouseAdapter setupTempChangeMotion() {
        return new MouseAdapter(){

            @Override
            public void mouseDragged(MouseEvent evt) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                double xDiff = evt.getX() - SpriteAnim.this._posx;
                SpriteAnim.this._posx = evt.getX();
                digimon.setTempGoal((int)((double)digimon.getTempGoal() + xDiff));
                SpriteAnim.this.setupTempMenu(digimon.getTempGoal());
            }
        };
    }

    private void cursorTempMove() {
        PhysicalState digimon;
        if (!this._tempDrag) {
            digimon = this._controller.getModel().getDigimon();
            digimon.setTempGoal(digimon.getTemp());
        }
        this._tempDrag = true;
        digimon = this._controller.getModel().getDigimon();
        if (digimon.getTempGoal() + 1 > Config._maxTemp) {
            digimon.setTempGoal(0);
        } else {
            digimon.setTempGoal(digimon.getTempGoal() + 1);
        }
        this.setupTempMenu(digimon.getTempGoal());
    }

    private MouseAdapter setupTempChangeListener() {
        return new MouseAdapter(){
            int firstX;
            int firstY;

            @Override
            public void mousePressed(MouseEvent e) {
                PhysicalState digimon;
                digimon.setTempGoal((digimon = SpriteAnim.this._controller.getModel().getDigimon()).getTempGoal() > 100 ? digimon.getTemp() : digimon.getTempGoal());
                SpriteAnim.this._tempDrag = true;
                SpriteAnim.this.setupTempMenu(digimon.getTempGoal());
                if (SpriteAnim.this._keyboard.getCPressed()) {
                    SpriteAnim.this.cursorTempMove();
                }
                SpriteAnim.this._posx = e.getX();
                Point p = MouseInfo.getPointerInfo().getLocation();
                this.firstX = p.x;
                this.firstY = p.y;
                SpriteAnim.this._sounds.playSound(SoundConfig._click);
                if (!SpriteAnim.this._keyboard.getCPressed()) {
                    try {
                        SpriteAnim.this._interact.setCursor(SpriteAnim.this._interact.getToolkit().createCustomCursor(new BufferedImage(1, 1, 2), new Point(), null));
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
            }

            @Override
            public void mouseEntered(MouseEvent e) {
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                PhysicalState digimon = SpriteAnim.this._controller.getModel().getDigimon();
                if (digimon.getTempGoal() == digimon.getTemp()) {
                    digimon.setTempGoal(101);
                }
                SpriteAnim.this.setupTempMenu(digimon.getTemp());
                SpriteAnim.this._tempDrag = false;
                try {
                    Robot r = new Robot();
                    r.mouseMove(this.firstX, this.firstY);
                    SpriteAnim.this._interact.setCursor(Cursor.getDefaultCursor());
                }
                catch (AWTException aWTException) {
                }
                catch (Exception exception) {
                    // empty catch block
                }
            }
        };
    }

    private int getNumInPage(Enum.Menu menu) {
        return menu == Enum.Menu.EvolutionInventory ? 1 : 4;
    }

    private int getConsumableIndex(Enum.Menu menu, SpriteObj button) {
        int numInPage = this.getNumInPage(menu);
        int i = this.getConsumableButtonIndex(button);
        return i + numInPage * this._consumablePage;
    }

    private ShopConsumable assignConsumableTypes(SpriteObj button, Enum.Menu menu) {
        ShopConsumable sc = null;
        PhysicalState digimon = this._controller.getModel().getDigimon();
        int i = this.getConsumableIndex(menu, button);
        boolean food = menu.toString().toLowerCase().contains("food");
        boolean shop = menu.toString().toLowerCase().contains("shop");
        boolean sell = menu.toString().toLowerCase().contains("sell");
        if (food) {
            if (shop) {
                this._consumableType = digimon.getHomeFoodShop().get(i);
                this._foodType = this._consumableType.getFood(digimon.getFoodTypes());
                sc = this._consumableType;
            } else if (sell) {
                this._consumableType = digimon.getSellableFood().get(i);
                this._foodType = this._consumableType.getFood(digimon.getFoodTypes());
                sc = this._consumableType;
            } else {
                this._foodType = digimon.getFoodOwned(true).get(i);
                sc = this._foodType.getHomeShop();
            }
        } else if (shop) {
            this._consumableType = digimon.getHomeItemShop().get(i);
            this._itemType = this._consumableType.getItem(digimon.getItems());
            sc = this._consumableType;
        } else if (sell) {
            this._consumableType = digimon.getSellableItems().get(i);
            this._itemType = this._consumableType.getItem(digimon.getItems());
            sc = this._consumableType;
        } else {
            boolean evol = menu.toString().toLowerCase().contains("evolution");
            this._itemType = evol ? digimon.getItemsOwned(digimon.getEvolItems(true)).get(i) : digimon.getItemsOwned(digimon.getNormalItems(true)).get(i);
            sc = this._itemType.getHomeShop();
        }
        return sc;
    }

    private int getConsumableButtonIndex(SpriteObj button) {
        int i = -1;
        if (button.equals(this._meatButton)) {
            i = 0;
        } else if (button.equals(this._fishButton)) {
            i = 1;
        } else if (button.equals(this._fruitButton)) {
            i = 2;
        } else if (button.equals(this._vegButton)) {
            i = 3;
        }
        return i;
    }

    private boolean canInteract() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        return this._controller.isPlaying() && digimon.getAlive() && digimon.getGrowthStage() != Enum.Stage.Egg;
    }

    public void freeStartMenuResources() {
        this._eggLabel.setSpriteSheet(null);
        this._eggLabel.setSpriteLoc(null);
        this.remove(this._saveLoadMenu);
        this.remove(this._newGameMenu);
        this.remove(this._startButton);
        this.remove(this._loadButton);
        this.remove(this._difficultyMenu);
        this.remove(this._timeSkipButton);
        this._difficultyMenu.setVisible(false);
        this._newGameMenu.setVisible(false);
        this._saveLoadMenu.setVisible(false);
        this._startButton = null;
        this._loadButton = null;
        this._saveLoadMenu = null;
        this._newGameMenu = null;
        this._difficultyMenu = null;
        this._userInputTitle.setVisible(false);
        this.requestFocus();
    }
}

