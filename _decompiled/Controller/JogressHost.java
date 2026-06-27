/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.ClockTic;
import Controller.JogressProtocol;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Socket;

public class JogressHost
extends JogressProtocol {
    private Socket _clientSocket;
    private Thread _thread;

    public Thread getThread() {
        return this._thread;
    }

    public Socket getClientSocket() {
        return this._clientSocket;
    }

    public JogressHost(ClockTic controller, String jogressMatch, String port) {
        super(controller, jogressMatch);
        super.setupServerSocket(Integer.parseInt(port));
        this._thread = new Thread(new Runnable(){

            @Override
            public void run() {
                try {
                    if (JogressHost.this._clientSocket == null) {
                        JogressHost.this._clientSocket = JogressHost.this._serverSocket.accept();
                    }
                    if (JogressHost.this._clientSocket.isConnected()) {
                        JogressHost.this.startJogress();
                    }
                    if (JogressHost.this._thread != null) {
                        JogressHost.this._thread.interrupt();
                    }
                }
                catch (Exception e) {
                    if (JogressHost.this._controller != null) {
                        JogressHost.this._controller.onError(false);
                    }
                    e.printStackTrace();
                }
            }
        });
        this._thread.start();
    }

    public void startJogress() {
        try {
            this._output = new BufferedWriter(new OutputStreamWriter(this._clientSocket.getOutputStream()));
            this._input = new BufferedReader(new InputStreamReader(this._clientSocket.getInputStream()));
            this._output.write("Jogress Start");
            this._output.newLine();
            this._output.flush();
            super.sendPlayerInfo(this._output);
            super.receivePartnerInfo(this._input);
            if (super.jogressFindFusionsAndAttributes()) {
                this._output.write(this._jogressMatch);
                this._output.newLine();
                this._output.flush();
            }
            if (!this._jogressMatch.equals("")) {
                this._controller.getView().setFrame(0);
                super.checkJogress();
                this._isConnection = true;
            } else {
                this._controller.onMismatch();
            }
        }
        catch (Exception e) {
            if (this._controller != null) {
                this._controller.onError(false);
            }
            e.printStackTrace();
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

