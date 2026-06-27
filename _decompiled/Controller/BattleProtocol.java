/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.ClockTic;
import Model.Config;
import Model.CrashEntry;
import Model.Enemy;
import Model.Enum;
import Model.PhysicalState;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ServerSocket;

public class BattleProtocol {
    protected ClockTic _controller;
    public int BATTLE_START = -842213;
    public DataInputStream _input;
    public DataOutputStream _output;
    protected boolean _isConnection;
    protected Enemy _player;
    protected Enemy _opponent;
    protected String _oppChecksum;
    protected boolean _oppGameMod;
    protected int _oppDiff;
    protected boolean _multiBattle = true;
    protected ServerSocket _serverSocket;

    public String getOppChecksum() {
        return this._oppChecksum;
    }

    public boolean getOppGameMod() {
        return this._oppGameMod;
    }

    public int getOppDiff() {
        return this._oppDiff;
    }

    public boolean getMultiBattle() {
        return this._multiBattle;
    }

    public BattleProtocol(ClockTic controller) {
        this._controller = controller;
        this.setupPlayer();
    }

    public void setupServerSocket(int port) {
        block2: {
            try {
                this._serverSocket = new ServerSocket(port);
            }
            catch (Exception e) {
                CrashEntry.generateEntry(e);
                e.printStackTrace();
                if (this._controller == null) break block2;
                this._controller.onError(true);
            }
        }
    }

    public Enum.Attribute waitTurn(int playerAttack) {
        block3: {
            try {
                boolean surrendered = false;
                this._output.writeBoolean(false);
                surrendered = this._input.readBoolean();
                if (!surrendered) {
                    this.sendAttack(this._output, playerAttack);
                    return this.receiveAttack(this._input);
                }
                this._controller.onError(true);
            }
            catch (Exception e) {
                e.printStackTrace();
                if (this._controller == null) break block3;
                this._controller.onError(true);
            }
        }
        return Enum.Attribute.NA;
    }

    public Enum.Attribute receiveAttack(DataInputStream input) {
        try {
            int attType = input.readInt();
            return Enum.Attribute.values()[attType];
        }
        catch (Exception e) {
            e.printStackTrace();
            if (this._controller != null) {
                this._controller.onError(true);
            }
            return Enum.Attribute.NA;
        }
    }

    public void sendAttack(DataOutputStream output, int attack) {
        block2: {
            try {
                output.writeInt(attack);
            }
            catch (Exception e) {
                e.printStackTrace();
                if (this._controller == null) break block2;
                this._controller.onError(true);
            }
        }
    }

    public void setupPlayer() {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        this._player = new Enemy();
        int bonus = digimon.getIsFree() ? 1 : 0;
        int powerBonus = Config._pvpBonusPowerMultiple;
        byte health = digimon.getHealthPoints();
        this._player.setEnemyHealth(health);
        this._player.setOppAttribute(digimon.getAttribute());
        this._player.setOppField(digimon.getField());
        this._player.setOppElement(digimon.getElement());
        this._player.setOppGreen((digimon.getDataPower() + bonus) * powerBonus);
        this._player.setOppRed((digimon.getVaccinePower() + bonus) * powerBonus);
        this._player.setOppYellow((digimon.getVirusPower() + bonus) * powerBonus);
        this._player.setOppStage(digimon.getGrowthStage());
        this._player.setSpriteNum(digimon.getSpriteNum());
        this._player.setSpriteSet(digimon.getSpriteSet());
        this._player.setIsSick(digimon.isSick());
        this._player.setIndex(digimon.getIndex());
    }

    public void receiveOpponentInfo(DataInputStream input) {
        block2: {
            try {
                this._opponent = new Enemy();
                this._opponent.setEnemyHealth(input.readInt());
                this._opponent.setOppAttribute(Enum.Attribute.values()[input.readInt()]);
                this._opponent.setOppField(Enum.Field.values()[input.readInt()]);
                this._opponent.setOppElement(Enum.Element.values()[input.readInt()]);
                this._opponent.setOppGreen(input.readInt());
                this._opponent.setOppRed(input.readInt());
                this._opponent.setOppYellow(input.readInt());
                this._opponent.setOppStage(Enum.Stage.values()[input.readInt()]);
                this._opponent.setSpriteNum(input.readInt());
                this._opponent.setSpriteSet(input.readInt());
                this._opponent.setIsSick(input.readBoolean());
                this._opponent.setIndex(input.readInt());
                this._oppChecksum = input.readUTF();
                this._oppGameMod = input.readBoolean();
                this._oppDiff = input.readInt();
            }
            catch (Exception e) {
                e.printStackTrace();
                if (this._controller == null) break block2;
                this._controller.onError(true);
            }
        }
    }

    public void sendPlayerInfo(DataOutputStream output) {
        block3: {
            if (this._player != null) {
                try {
                    output.writeInt(this._player.getEnemyHealth());
                    output.writeInt(this._player.getOppAttribute().ordinal());
                    output.writeInt(this._player.getOppField().ordinal());
                    output.writeInt(this._player.getOppElement().ordinal());
                    output.writeInt(this._player.getOppGreen());
                    output.writeInt(this._player.getOppRed());
                    output.writeInt(this._player.getOppYellow());
                    output.writeInt(this._player.getOppStage().ordinal());
                    output.writeInt(this._player.getSpriteNum());
                    output.writeInt(this._player.getSpriteSet());
                    output.writeBoolean(this._player.getIsSick());
                    output.writeInt(this._player.getIndex());
                    PhysicalState digimon = this._controller.getModel().getDigimon();
                    output.writeUTF(digimon.getChecksum());
                    output.writeBoolean(digimon.getGameModified());
                    output.writeInt(digimon.getDifficultySetting());
                }
                catch (Exception e) {
                    e.printStackTrace();
                    if (this._controller == null) break block3;
                    this._controller.onError(true);
                }
            }
        }
    }

    public void dispose() {
        try {
            if (this._input != null) {
                this._input.close();
            }
            if (this._output != null) {
                this._output.close();
            }
            if (this._serverSocket != null) {
                this._serverSocket.close();
            }
        }
        catch (IOException iOException) {
            // empty catch block
        }
        this._controller = null;
        this._input = null;
        this._output = null;
        this._player = null;
        this._opponent = null;
        this._serverSocket = null;
    }
}

