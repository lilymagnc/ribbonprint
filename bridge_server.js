const express = require('express');
const cors = require('cors');
// 추후 윈도우 인쇄를 위한 child_process 또는 node-printer 등을 활용할 예정입니다.
const { exec } = require('child_process');

const app = express();
const port = 8000;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.send({ status: 'ok', message: 'Node.js Print Bridge Agent is running' });
});

app.post('/api/print', (req, res) => {
  // 웹 앱에서 전달받을 데이터: 프린터 이름, 각 텍스트 블록 정보 등
  const printData = req.body;
  console.log('Received print request:', printData);
  
  // TODO: 실제 윈도우 프린터(win32print 대안)로 전송하는 로직 구현 필요
  // 지금은 단순히 성공 메시지를 응답하여 E2E 테스트 통신 여부를 확인합니다.
  
  res.json({
      status: 'success',
      message: 'Print job simulated successfully in Node Bridge',
      data: printData
  });
});

app.listen(port, () => {
  console.log(`Print Bridge listening at http://localhost:${port}`);
});
