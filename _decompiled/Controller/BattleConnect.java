/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.BattleProtocol;
import Controller.ClockTic;
import Controller.Utility;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;

public class BattleConnect
extends BattleProtocol {
    private Socket _clientSocket;
    private InetSocketAddress _socketAddress;

    public Socket getClientSocket() {
        return this._clientSocket;
    }

    public InetSocketAddress getSocketAddress() {
        return this._socketAddress;
    }

    public BattleConnect(ClockTic controller, String hostName) {
        super(controller);
        this._socketAddress = Utility.getSocketAddress(hostName);
    }

    private boolean attemptConnection() {
        try {
            boolean battleStart;
            block8: {
                battleStart = false;
                this._input = new DataInputStream(this._clientSocket.getInputStream());
                this._output = new DataOutputStream(this._clientSocket.getOutputStream());
                try {
                    this._clientSocket.setSoTimeout(5000);
                    int uniqueStart = this._input.readInt();
                    if (uniqueStart == this.BATTLE_START) {
                        battleStart = true;
                    } else {
                        this._controller.onError(true);
                    }
                }
                catch (Exception exc) {
                    exc.printStackTrace();
                    if (this._controller == null) break block8;
                    this._controller.onError(true);
                }
            }
            if (battleStart) {
                super.receiveOpponentInfo(this._input);
                super.sendPlayerInfo(this._output);
                this._controller.multiBattleStartConnector(this._opponent, this._oppDiff);
                this._clientSocket.setSoTimeout(0);
            }
            return battleStart;
        }
        catch (Exception e) {
            e.printStackTrace();
            if (this._controller != null) {
                this._controller.onError(true);
            }
            return false;
        }
    }

    public boolean checkBattleStart() {
        block4: {
            try {
                if (this._clientSocket != null && this._clientSocket.isConnected()) {
                    return this.attemptConnection();
                }
                this._clientSocket = new Socket();
                this._clientSocket.connect(this._socketAddress);
                if (this._clientSocket != null && this._clientSocket.isConnected()) {
                    return this.attemptConnection();
                }
            }
            catch (Exception e) {
                e.printStackTrace();
                if (this._controller == null) break block4;
                this._controller.onError(true);
            }
        }
        return false;
    }

    @Override
    public void dispose() {
        try {
            if (this._clientSocket != null) {
                this._clientSocket.close();
            }
        }
        catch (IOException iOException) {
            // empty catch block
        }
        this._clientSocket = null;
        this._socketAddress = null;
        super.dispose();
    }
}

