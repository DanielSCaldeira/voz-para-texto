"""Define volume do microfone padrão para 100% via Core Audio API."""

import subprocess

_PS_SCRIPT = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
[Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int NotImpl1();
    [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    [PreserveSig] int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int NotImpl1(); int NotImpl2();
    [PreserveSig] int SetMasterVolumeLevelScalar(float fLevel, ref Guid pguidEventContext);
}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject {}
public class MicAudio {
    static readonly IMMDeviceEnumerator e = (IMMDeviceEnumerator)(new MMDeviceEnumeratorComObject());
    public static void SetVolume(float level) {
        IMMDevice dev; e.GetDefaultAudioEndpoint(1, 1, out dev);
        Guid iid = typeof(IAudioEndpointVolume).GUID; object o;
        dev.Activate(ref iid, 23, IntPtr.Zero, out o);
        IAudioEndpointVolume vol = (IAudioEndpointVolume)o;
        Guid empty = Guid.Empty;
        vol.SetMasterVolumeLevelScalar(level, ref empty);
    }
}
"@
[MicAudio]::SetVolume(1.0)
"""


def set_max_volume() -> None:
    try:
        subprocess.run(["powershell", "-Command", _PS_SCRIPT], capture_output=True, timeout=10)
        print("Microfone definido para volume máximo.")
    except Exception as e:
        print(f"Aviso: não foi possível ajustar o volume: {e}")
