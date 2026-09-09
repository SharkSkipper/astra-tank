export const SYSTEMS = [
  { id: 'hull', label: '车体与装甲', english: 'HULL & ARMOR', color: '#97b9a3', description: '焊接车体、底板、挡泥板与侧裙板，组成车体的主要外部轮廓。' },
  { id: 'turret', label: '炮塔总成', english: 'TURRET ASSEMBLY', color: '#c9b27b', description: '焊接炮塔壳体、座圈、舱盖与顶部附件，保留独立的炮塔旋转轴心。' },
  { id: 'gun', label: '主炮与炮盾', english: 'GUN & MANTLET', color: '#f0a786', description: '炮管外形、空心炮口与炮盾，随炮管俯仰轴心整体运动。口径和隐藏机构未经实车验证。' },
  { id: 'track-left', label: '左侧履带', english: 'LEFT TRACK', color: '#78bdd1', description: '85 节独立履带，由金属履带板、橡胶垫和导向齿组成。链接实例共享几何数据。' },
  { id: 'track-right', label: '右侧履带', english: 'RIGHT TRACK', color: '#e9c77b', description: '85 节独立履带，沿闭合路径环绕前导向轮、负重轮和后主动轮。' },
  { id: 'running-gear', label: '轮组与悬挂', english: 'RUNNING GEAR', color: '#a5b0dd', description: '两侧各七对负重轮，以及前导向轮、后主动轮、托带轮和外露悬挂连接件。' },
  { id: 'engine-deck', label: '动力舱外部', english: 'ENGINE DECK', color: '#80c6a0', description: '车尾双圆形风扇、开放式格栅、百叶窗、排气口与检修盖。模型不含内部发动机。' },
  { id: 'optics', label: '观瞄与传感', english: 'OPTICS & SENSORS', color: '#78d3da', description: '潜望镜、主瞄准镜、侧面光学窗口、横风传感器及天线的外部形态。' },
  { id: 'equipment', label: '随车设备', english: 'EXTERNAL EQUIPMENT', color: '#d89fab', description: '牵引索、工具、储物箱、灯具、烟幕装置与顶部机枪等外部附件。' },
];

export const MODEL_METADATA = {
  title: '豹 2 早期原型车',
  english: 'LEOPARD 2 · EARLY PROTOTYPE',
  source: '用户四向参考图与同系列原型车公开照片',
  scope: '外观重建模型；具体 PT 车体号与 T 炮塔号尚未确认，不含经验证的内部结构。',
  units: 'm',
  dimensions: { length: 9.613, width: 3.7, height: 3.358 },
  sourceNodes: 1916,
  logicalParts: 1857,
  renderMeshes: 2197,
  uniqueMeshes: 1688,
  trackLinksPerSide: 85,
  roadWheelStationsPerSide: 7,
  frontAxis: '-X',
  upAxis: '+Y',
  leftAxis: '-Z',
};

function sourceName(meshName) {
  return String(meshName || '').replace(/\.\d{3}$/, '');
}

export function getSystemId(meshName) {
  const name = sourceName(meshName);
  if (/^L_TrackLink_/.test(name)) return 'track-left';
  if (/^R_TrackLink_/.test(name)) return 'track-right';
  if (/RoadWheel|FrontIdler|RearDriveSprocket|ReturnRoller|SuspensionAxle|TrailingArm|RunningGear/.test(name)) return 'running-gear';
  if (/^(Gun_|Mantlet_)/.test(name)) return 'gun';
  if (/Fan_|Engine_Louvre|Rear_Exhaust|Rear_Engine_Deck|Rear_Service/.test(name)) return 'engine-deck';
  if (/Periscope|Primary_Sight|Side_Optical|Optic_FrameBolt|Crosswind_Sensor|Radio_Antenna/.test(name)) return 'optics';
  if (/Turret_|Roof_Weld|Lower_Weld|Roof_Grab|Rear_Stowage|Commander_|Loader_|Bustle_/.test(name)) return 'turret';
  if (/^Hull_|Lower_Belly|Bow_Center|Driver_Hatch|FullLength_Fender|Fender_Outer|Front_Mudguard|Rear_RubberFlap|Rear_FlapClamp|FlapBolt|Skirt_/.test(name)) return 'hull';
  return 'equipment';
}

const labels = {
  Bow_Center_AccessPlate: '车首中央检修板',
  Bow_SpareTrack_Block: '车首备用履带板',
  Bow_SpareTrack_Pad: '车首备用履带橡胶垫',
  Driver_Hatch_Handle: '驾驶员舱盖把手',
  Driver_Hatch_Lid: '驾驶员舱盖',
  Driver_Hatch_Seal: '驾驶员舱盖密封圈',
  Driver_Periscope: '驾驶员潜望镜外壳',
  Driver_Periscope_Glass: '驾驶员潜望镜镜片',
  Hull_Main_WeldedShell: '焊接车体主壳',
  Lower_Belly_Plate: '车底板',
  Cable_Clamp: '牵引索固定夹',
  Cable_Eye: '牵引索端环',
  Engine_Louvre: '动力舱百叶片',
  Engine_Louvre_Recess: '动力舱百叶窗底座',
  Fan_Blade: '冷却风扇叶片',
  Fan_GridX: '风扇纵向格栅条',
  Fan_GridY: '风扇横向格栅条',
  Fan_Hub: '冷却风扇轮毂',
  Fan_Recess: '冷却风扇凹槽',
  Fan_Rim: '风扇格栅外环',
  Fan_RimBolt: '风扇外环螺栓',
  Fender_Outer_Seam: '挡泥板外缘接缝',
  Fender_Stowage: '翼子板储物箱',
  FlapBolt: '尾部挡泥帘螺栓',
  Front_Mudguard: '前挡泥板',
  FullLength_Fender: '全长翼子板',
  Headlight_Bezel: '前照灯饰圈',
  Headlight_Guard: '前照灯护架',
  Headlight_Housing: '前照灯外壳',
  Headlight_Lens: '前照灯镜片',
  PioneerTool_Head: '随车工具头部',
  PioneerTool_Shaft: '随车工具柄',
  Rear_Exhaust_Louvre: '尾部排气百叶片',
  Rear_Exhaust_Recess: '尾部排气口',
  Rear_FlapClamp: '尾部挡泥帘固定条',
  Rear_RubberFlap: '尾部橡胶挡泥帘',
  Rear_TailLamp: '尾灯',
  Skirt_Bolt: '侧裙板螺栓',
  Skirt_Hinge: '侧裙板铰链',
  Skirt_Panel: '侧裙板',
  Stowage_Clasp: '储物箱搭扣',
  Stowage_Lid: '储物箱盖',
  Tow_Lug: '牵引耳座',
  Tow_Shackle: '牵引卸扣',
  TowCable_Main: '牵引钢索',
  Rear_Engine_Deck_Separator: '尾部动力舱中央分隔条',
  Rear_Service_Access_Hatch: '尾部检修盖',
  Rear_Service_Handle: '尾部检修盖把手',
  SuspensionAxle: '悬挂轴',
  TrailingArm: '悬挂摆臂',
  ReturnRollerHub: '托带轮轮毂',
  ReturnRollerRubber: '托带轮橡胶轮缘',
  Bustle_Rail_Standoff: '炮塔尾部护栏支撑',
  Crosswind_Sensor_Base: '横风传感器底座',
  Crosswind_Sensor_Foot: '横风传感器连接座',
  Crosswind_Sensor_Head: '横风传感器环形头部',
  Crosswind_Sensor_HeadCross: '横风传感器横杆',
  Crosswind_Sensor_Mast: '横风传感器桅杆',
  Gun_Bore_Interior: '炮口内部遮光面',
  Gun_Collar_Seam: '炮管套环接缝',
  Gun_ExternalTube_HollowMuzzle: '主炮炮管与空心炮口',
  Gun_Mantlet_Armored_Shield: '主炮装甲炮盾',
  Gun_Mantlet_Collar: '炮盾连接套环',
  Mantlet_CollarBolt: '炮盾套环螺栓',
  Lower_Weld: '炮塔下缘焊缝',
  Optic_FrameBolt: '侧面光学窗口框架螺栓',
  Rear_Stowage_Lid: '炮塔尾部储物箱盖',
  Roof_Grab: '炮塔顶部扶手',
  Roof_Weld: '炮塔顶部焊缝',
  Side_Optical_Glass: '侧面光学窗口镜片',
  Side_Optical_Housing: '侧面光学窗口外壳',
  Side_Optical_Rim: '侧面光学窗口边框',
  Smoke_Rack: '烟幕装置安装架',
  SmokeCap: '烟幕筒端盖',
  SmokeMount: '烟幕筒安装螺栓',
  SmokeRim: '烟幕筒端环',
  SmokeTube: '烟幕筒外壳',
  Turret_Grab: '炮塔侧面扶手',
  Turret_LiftingEye: '炮塔吊环',
  Turret_Rear_Stowage: '炮塔尾部储物箱',
  Turret_Side_Seam: '炮塔侧面接缝',
  Primary_Sight_Glass: '主瞄准镜镜片',
  Primary_Sight_Housing: '主瞄准镜外壳',
  Primary_Sight_Plinth: '主瞄准镜底座',
  Primary_Sight_Shade: '主瞄准镜遮檐',
  Primary_Sight_Shadow: '主瞄准镜凹槽',
  Radio_Antenna_Base: '无线电天线底座',
  Radio_Antenna_Spring: '无线电天线弹簧环',
  Radio_Antenna_Whip: '无线电鞭状天线',
  Roof_MG_Barrel: '顶部机枪枪管外形',
  Roof_MG_FeedBox: '顶部机枪弹箱外形',
  Roof_MG_FrontSight: '顶部机枪准星外形',
  Roof_MG_JacketRing: '顶部机枪护套环',
  Roof_MG_Muzzle: '顶部机枪枪口外形',
  Roof_MG_Pintle: '顶部机枪支架',
  Roof_MG_Receiver: '顶部机枪机匣外形',
  Roof_MG_Stock: '顶部机枪枪托外形',
  Turret_Bustle_ProtectionRail: '炮塔尾部保护栏',
  Turret_Main_WeldedShell: '焊接炮塔主壳',
  Turret_Rear_Vent_Recess: '炮塔尾部通风口',
  Turret_Rear_Vent_Slat: '炮塔尾部通风栅片',
  Turret_Roof_Bolt: '炮塔顶部螺栓',
  Turret_Race_Lower: '炮塔下座圈',
  Turret_Race_Upper: '炮塔上座圈',
};

const wheelLabels = {
  RubberTire: '橡胶轮缘', DishedRim: '盘形轮辋', RimLip: '轮辋唇边',
  BearingRing: '轴承环', Hub: '轮毂', HubCap: '轮毂盖', AxleCover: '轴端盖',
  HubBolt: '轮毂螺栓', RimBolt: '轮辋螺栓', BearingCap: '轴承盖',
  Flange: '轮缘凸边', RunningRim: '行走轮缘', Spoke: '辐条',
  Axle: '轮轴', DriveTooth: '驱动齿', Fastener: '紧固螺栓',
  ToothRing: '齿圈', WebRim: '辐板外环', WebSpoke: '辐板支撑',
};

const hatchLabels = {
  Center_Boss: '舱盖中央凸台', Hatch_Grab: '舱盖把手', Hatch_Lid: '舱盖',
  Hatch_Lip: '舱盖边缘环', Hatch_Ring: '舱口座圈', Hatch_Seal: '舱口密封圈',
  Hinge: '舱盖铰链', Hinge_Pin: '舱盖铰链销', Latch_Spoke: '舱盖锁紧辐条',
  Periscope: '潜望镜外壳', Periscope_Lens: '潜望镜镜片',
};

const oneBased = new Set(['Fender_Stowage', 'Stowage_Lid', 'Skirt_Panel', 'SuspensionAxle', 'TrailingArm', 'ReturnRollerHub', 'ReturnRollerRubber']);
const zeroBased = new Set(['Driver_Periscope', 'Driver_Periscope_Glass', 'Engine_Louvre', 'Fan_Blade', 'Fan_RimBolt', 'Rear_Exhaust_Louvre', 'Turret_Rear_Vent_Slat', 'Radio_Antenna_Spring', 'Roof_MG_JacketRing']);

export function getPartLabel(meshName) {
  const name = sourceName(meshName);
  const side = name.startsWith('L_') ? '左侧' : name.startsWith('R_') ? '右侧' : '';
  const stem = name.replace(/^[LR]_/, '');
  let match;
  if ((match = /^TrackLink_(\d+)/.exec(stem))) return `${side}履带节 ${Number(match[1])}`;
  if ((match = /^RoadWheel_(\d+)_(Inner|Outer)_(\w+?)(?:_(\d+))?$/.exec(stem))) {
    return `${side}第 ${Number(match[1])} 组${match[2] === 'Inner' ? '内' : '外'}负重轮${wheelLabels[match[3]] || match[3]}${match[4] ? ` ${Number(match[4])}` : ''}`;
  }
  if ((match = /^(FrontIdler|RearDriveSprocket)_(\w+?)(?:_([+-]?\d+))?(?:_(\d+))?$/.exec(stem))) {
    const wheel = match[1] === 'FrontIdler' ? '前导向轮' : '后主动轮';
    // Signed half labels encode global transverse halves, not universal inner/outer sides.
    const half = match[3] ? `${(Number(match[3]) > 0) === (side === '左侧') ? '外' : '内'}侧` : '';
    return `${side}${wheel}${half}${wheelLabels[match[2]] || match[2]}${match[4] ? ` ${Number(match[4])}` : ''}`;
  }
  if ((match = /^(Commander|Loader)_(.+?)(?:_(\d+))?$/.exec(stem))) {
    return `${match[1] === 'Commander' ? '车长' : '装填手'}${hatchLabels[match[2]] || match[2]}${match[3] ? ` ${Number(match[3]) + 1}` : ''}`;
  }
  const tokens = stem.split('_');
  const numbers = tokens.filter(token => /^[+-]?\d+(?:\.\d+)?$/.test(token)).map(Number);
  const key = tokens.filter(token => !/^[+-]?\d+(?:\.\d+)?$/.test(token)).join('_');
  const label = labels[key] || '外部部件';
  let suffix = '';
  if (oneBased.has(key) && numbers.length) suffix = ` ${numbers[0]}`;
  else if (zeroBased.has(key) && numbers.length) suffix = ` ${numbers[0] + 1}`;
  else if (/^Fan_Grid[XY]$/.test(key)) suffix = ` ${numbers[0] + 14}`;
  else if (/^Smoke/.test(key) && numbers.length) suffix = numbers.length > 1 ? ` ${numbers[0] + 1}-${numbers[1] + 1}` : ` ${numbers[0] + 1}`;
  else if (['Skirt_Hinge', 'Skirt_Bolt', 'Stowage_Clasp'].includes(key)) suffix = ` ${numbers[0] + 1} / ${numbers[1]}`;
  else if (key === 'Turret_Roof_Bolt') suffix = ` ${numbers[0] > 0 ? '左' : '右'} ${numbers[1] + 1}`;
  else if (numbers.length) suffix = ` [${numbers.join(', ')}]`;
  return `${side}${label}${suffix}`;
}

export function getPartDescription(meshName) {
  const name = sourceName(meshName);
  if (/TrackLink/.test(name)) return '单节履带外部组件，包含履带板、橡胶垫、连接销外形及中央导向齿。每侧共 85 节；节距与细节来自外观建模估计。';
  if (/RoadWheel/.test(name)) return '双列负重轮的组成部件。每侧七个轮位，每个轮位包含内外两片轮体，中间留有履带导向齿间隙。';
  if (/FrontIdler/.test(name)) return '车体前端导向轮的组成部件，用于表达履带前端转向路径；轮毂、辐条及紧固件均保留独立外形。';
  if (/RearDriveSprocket/.test(name)) return '车体后端主动轮的组成部件，外部齿圈与履带相邻。模型展示轮齿、辐板、轮毂和连接件，不含内部传动机构。';
  if (/ReturnRoller/.test(name)) return '上支履带路径下方的托带轮部件，每侧四组，包含橡胶轮缘和轮毂。';
  if (/SuspensionAxle|TrailingArm/.test(name)) return '负重轮与车体之间的外露悬挂连接件。隐藏部分及实际运动机构未建模。';
  if (/Gun_ExternalTube/.test(name)) return '根据参考图重建的炮管外形，保留阶梯式排烟装置轮廓与空心炮口。图纸不能确定原型车炮管口径，几何尺寸仅用于外观展示。';
  if (/Gun_Bore/.test(name)) return '位于炮口内部的深色遮光面，用于表达空心管腔的视觉深度，不代表真实炮膛结构。';
  if (/^(Gun_|Mantlet_)/.test(name)) return '主炮外部总成的独立部件，随 Gun_Elevation_Pivot 俯仰。炮盾与套环形状按参考图解释重建。';
  if (/Fan_/.test(name)) return '尾部双圆形冷却风扇组件的一部分，叶片位于实际开放的交叉格栅下方，格栅与紧固件可独立选择。';
  if (/Engine_Louvre|Rear_Exhaust|Rear_Engine_Deck|Rear_Service/.test(name)) return '车尾动力舱外部的通风、排气或检修附件。仅重建外部形态，内部发动机和动力传动系统不在模型范围内。';
  if (/Periscope|Primary_Sight|Side_Optical|Optic_FrameBolt/.test(name)) return '乘员观察或瞄准装置的外部构件，镜片、框架与外壳分别建模；内部光学元件未建模。';
  if (/Crosswind_Sensor/.test(name)) return '按参考图轮廓补充的炮塔顶部横风设备外形，包含底座、细桅杆和头部，具体型号未经确认。';
  if (/Radio_Antenna/.test(name)) return '炮塔顶部无线电天线的外部构件，包含底座、弹簧环和柔性鞭状天线外形。';
  if (/Smoke/.test(name)) return '炮塔侧面的烟幕装置外部部件，每侧两排、每排四个筒体，保留安装架、端盖与紧固件。';
  if (/Roof_MG/.test(name)) return '顶部机枪的外部轮廓部件，按展示需要重建；不包含内部机构。';
  if (/Tow|Cable/.test(name)) return '车体外部牵引与固定附件，钢索沿翼子板铺设，端环、固定夹及牵引耳保留独立对象。';
  if (/Hatch|Commander_|Loader_/.test(name)) return '乘员舱口外部组件，包括盖板、座圈、密封圈或连接件；模型当前保存为闭合外观。';
  if (/Headlight|TailLamp/.test(name)) return '车体外部灯具的独立部件，灯壳、镜片和保护结构依据参考图与同类原型车照片重建。';
  if (/SpareTrack/.test(name)) return '布置在车首上方的备用履带外形部件，履带板与橡胶垫分别保留。';
  if (/Stowage/.test(name)) return '车体或炮塔外部储物箱的组成部分，箱体、盖板及搭扣按外观分别建模。';
  return SYSTEMS.find(system => system.id === getSystemId(name)).description;
}

const explodeDirections = {
  hull: [0, 0, 0],
  turret: [0, 2.1, 0],
  gun: [-2.3, 2.1, 0],
  'track-left': [0, 0.15, -2.25],
  'track-right': [0, 0.15, 2.25],
  'running-gear': [0, -0.25, 0],
  'engine-deck': [1.3, 1.25, 0],
  optics: [0.1, 3.15, 0],
  equipment: [0.55, 0.7, 1.15],
};

export function getExplodeDirection(systemId) {
  return [...(explodeDirections[systemId] || [0, 0, 0])];
}
