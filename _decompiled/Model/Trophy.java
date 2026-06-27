/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;
import Model.Enum;
import Model.PhysicalState;

public class Trophy {
    private int _id = 0;
    private int _spriteNum = 0;
    private int _spriteSet = 0;
    private Enum.Season _season;
    private Enum.Field _fieldRestriction;
    private boolean _resetWon;
    private Enum.Attribute _attributeRestriction;
    private Enum.Time _time;
    private Enum.Stage _ageLimit;
    private Enum.Stage _enemyStage;
    private Enum.Field _enemyField;
    private Enum.Attribute _enemyAttribute;
    private Enum.Element _enemyElement;
    private double _bitModifier;
    private int _prelim;
    private int _item;
    private int[] _food = new int[2];
    private boolean _randomIncluded;
    private boolean _earned;
    private boolean _seasonBeat;
    private boolean _sameDayRetry;

    public int getID() {
        return this._id;
    }

    public int getSpriteNum() {
        return this._spriteNum;
    }

    public int getSpriteSet() {
        return this._spriteSet;
    }

    public Enum.Field getFieldRestriction() {
        return this._fieldRestriction;
    }

    public boolean getResetWon() {
        return this._resetWon;
    }

    public Enum.Attribute getAttributeRestriction() {
        return this._attributeRestriction;
    }

    public Enum.Time getTime() {
        return this._time;
    }

    public Enum.Season getSeason() {
        return this._season;
    }

    public double getBitModifier() {
        return this._bitModifier;
    }

    public Enum.Stage getAgeLimit() {
        return this._ageLimit;
    }

    public Enum.Stage getEnemyStage() {
        return this._enemyStage;
    }

    public Enum.Attribute getEnemyAttribute() {
        return this._enemyAttribute;
    }

    public Enum.Element getEnemyElement() {
        return this._enemyElement;
    }

    public Enum.Field getEnemyField() {
        return this._enemyField;
    }

    public boolean getSameDayRetry() {
        return this._sameDayRetry;
    }

    public int getPrelim() {
        return this._prelim;
    }

    public int getItem() {
        return this._item;
    }

    public int[] getFood() {
        return this._food;
    }

    public boolean getRandomIncluded() {
        return this._randomIncluded;
    }

    public boolean getSeasonBeat() {
        return this._seasonBeat;
    }

    public void setSeasonBeat(boolean b) {
        this._seasonBeat = b;
    }

    public boolean getEarned() {
        return this._earned;
    }

    public void setEarned(boolean b) {
        this._earned = b;
    }

    public Trophy() {
        this._season = Enum.Season.Winter;
    }

    public int[] getMinMaxBits(PhysicalState digimon) {
        int[] range = new int[2];
        int roster = 7;
        Enum.Stage s = this._enemyStage == Enum.Stage.None ? (this._ageLimit == Enum.Stage.None ? this.getStageByAge(digimon) : this._ageLimit) : this._enemyStage;
        switch (s) {
            case Rookie: {
                range[1] = (int)((double)(roster * Config._tourneyRookieBits) * this._bitModifier);
                break;
            }
            case Champion: {
                range[1] = (int)((double)(roster * Config._tourneyChampBits) * this._bitModifier);
                break;
            }
            case Ultimate: {
                range[1] = (int)((double)(roster * Config._tourneyUltBits) * this._bitModifier);
                break;
            }
            case Mega: {
                range[1] = (int)((double)(roster * Config._tourneyMegaBits) * this._bitModifier);
                break;
            }
            default: {
                range[1] = (int)((double)(roster * Config._tourneyMaxBits) * this._bitModifier);
            }
        }
        return range;
    }

    public int getAge() {
        switch (this._ageLimit) {
            case Rookie: {
                return Config._tourneyRandomRookieAge;
            }
            case Champion: {
                return Config._tourneyRandomChampAge;
            }
            case Ultimate: {
                return Config._tourneyRandomUltAge;
            }
            case Mega: {
                return Config._tourneyRandomMegaAge;
            }
        }
        return 0;
    }

    public Enum.Stage getStageByAge(PhysicalState digimon) {
        if (digimon.getAge() <= Config._tourneyRandomRookieAge) {
            return Enum.Stage.Rookie;
        }
        if (digimon.getAge() <= Config._tourneyRandomChampAge) {
            return Enum.Stage.Champion;
        }
        if (digimon.getAge() <= Config._tourneyRandomUltAge) {
            return Enum.Stage.Ultimate;
        }
        if (digimon.getAge() <= Config._tourneyRandomMegaAge) {
            return Enum.Stage.Mega;
        }
        return Enum.Stage.None;
    }

    public Trophy readInfoString(String trophy) {
        String[] info = trophy.split(",");
        this._id = Integer.parseInt(info[0]);
        this._spriteNum = Integer.parseInt(info[1]);
        this._spriteSet = Integer.parseInt(info[2]);
        this._season = Enum.Season.valueOf(info[3]);
        this._fieldRestriction = Enum.Field.valueOf(info[4]);
        this._resetWon = Boolean.parseBoolean(info[5]);
        this._attributeRestriction = Enum.Attribute.valueOf(info[6]);
        this._time = Enum.Time.valueOf(info[7]);
        this._ageLimit = Enum.Stage.valueOf(info[8]);
        this._bitModifier = Double.parseDouble(info[9]);
        this._prelim = Integer.parseInt(info[10]);
        this._item = Integer.parseInt(info[11]);
        String[] food = info[12].split("q");
        this._food[0] = Integer.parseInt(food[0]);
        this._food[1] = Integer.parseInt(food[1]);
        this._randomIncluded = Boolean.parseBoolean(info[13]);
        this._enemyStage = Enum.Stage.valueOf(info[14]);
        this._sameDayRetry = Boolean.parseBoolean(info[15]);
        this._enemyAttribute = Enum.Attribute.valueOf(info[16]);
        this._enemyElement = Enum.Element.valueOf(info[17]);
        this._enemyField = Enum.Field.valueOf(info[18]);
        return this;
    }
}

