import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

class EstimatedPowerApp extends Application.AppBase {

    private var _field as EstimatedPowerField or Null;

    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        _field = new EstimatedPowerField();
        return [_field as EstimatedPowerField];
    }

    function onSettingsChanged() as Void {
        if (_field != null) {
            (_field as EstimatedPowerField).loadSettings();
        }
        WatchUi.requestUpdate();
    }
}
