/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.BattleProtocol;
import Controller.ClockTic;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.Socket;

public class BattleHost
extends BattleProtocol {
    private Socket _clientSocket;
    private Thread _thread;

    public Thread getThread() {
        return this._thread;
    }

    public Socket getClientSocket() {
        return this._clientSocket;
    }

    public BattleHost(ClockTic controller, String port) {
        super(controller);
        super.setupServerSocket(Integer.parseInt(port));
        this._thread = new Thread(new Runnable(){

            @Override
            public void run() {
                block4: {
                    try {
                        if (BattleHost.this._clientSocket == null) {
                            BattleHost.this._clientSocket = BattleHost.this._serverSocket.accept();
                        }
                        if (BattleHost.this._clientSocket.isConnected()) {
                            BattleHost.this.startBattle();
                        }
                        BattleHost.this._thread.interrupt();
                    }
                    catch (Exception e) {
                        e.printStackTrace();
                        if (BattleHost.this._controller == null) break block4;
                        BattleHost.this._controller.onError(true);
                    }
                }
            }
        });
        this._thread.start();
    }

    public void startBattle() {
        block2: {
            try {
                this._output = new DataOutputStream(this._clientSocket.getOutputStream());
                this._input = new DataInputStream(this._clientSocket.getInputStream());
                this._output.writeInt(this.BATTLE_START);
                super.sendPlayerInfo(this._output);
                super.receiveOpponentInfo(this._input);
                this._controller.getView().setFrame(0);
                this._isConnection = true;
                this._controller.multiBattleStart(this._opponent, this._oppDiff);
            }
            catch (Exception e) {
                if (this._controller == null) break block2;
                e.printStackTrace();
                this._controller.onError(true);
            }
        }
    }

    @Override
    public void dispose() {
        try {
            if (this._thread != null) {
                this._thread.interrupt();
            }
            if (this._clientSocket != null) {
                this._clientSocket.close();
            }
        }
        catch (IOException iOException) {
            // empty catch block
        }
        this._clientSocket = null;
        this._thread = null;
        super.dispose();
    }
}

