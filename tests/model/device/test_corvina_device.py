
import json
import unittest

from model.device.corvina_device import CorvinaDevice


class CorvinaDeviceTestCase(unittest.TestCase):

    def test_deserialization(self):
        corvina_str = '[{"deviceId":"2WNJOs7r_bIV8JVZNp1ESw","realmId":"factoryal","tags":null,"creationDate":1745994688394,"updatedAt":1746429181138,"id":"tp52h9xcqK","configurationSent":true,"deleted":false,"orgResourceId":"factoryal","label":"DemoExorClusterVm","configurationApplied":true,"connected":false,"attributes":{"geoLocation":[45.377231681380174,11.048126220703125]},"lastConnUpdateAt":1746429543995,"configurationError":"","lastConfigUpdateAt":1746429195937,"modelId":"wdxDe8jJ9r","modelVersion":"1.0.0","modelName":"vigilant-banach-amazing-hamilton-EXORInternational","presetName":"EXORInternational_Mapping","presetId":"gJfFgChLmm","groups":[]},{"deviceId":"a9oyg23j1OJ05qEbhN8-fw","realmId":"factoryal","tags":null,"creationDate":1738683418265,"updatedAt":1759243330485,"id":"AzuUbIRrxs","configurationSent":true,"deleted":false,"orgResourceId":"factoryal","label":"FirstDemoGs02","configurationApplied":true,"connected":false,"attributes":{"vpn_inuse":false,"vpn_inuse_ts":1759385773718,"vpn_connected_ts":1759385773718,"vpn_connected":true,"geoLocation":[45.385057326253865,11.046752929687502]},"lastConfigUpdateAt":1759245727991,"configurationError":"","lastConnUpdateAt":1759246052346,"modelId":"Y0oAkxGwGu","modelVersion":"1.0.0","modelName":"Dummy","presetName":"DummyMapping","presetId":"AWnQS4LEL8","groups":[]}]'

        data = json.loads(corvina_str)

        for d in data:
            dm = CorvinaDevice.from_dict(d)
