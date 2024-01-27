const fs = require('fs');
const { Chart, registerables } = require('chart.js');
const { createCanvas, registerFont } = require('canvas');
const { Octokit } = require('@octokit/rest');
const { DateTime } = require("luxon");

const owner = 'owner'; //replace owner of repo
const repo = 'repo'; //replace with owner name
const branch = 'branch'; //replace with branch name
const token = 'token'; //replace with GitHub token
const n = 50; // replace with number of commits you want to fetch

const octokit = new Octokit({
  auth: token,
});

function formatDate(date, n) {
  // Parse the timestamp and convert it to the desired timezone
  const commitTime = DateTime.fromISO(date, { zone: 'utc' });
  const commitTimeLocal = commitTime.setZone('Europe/Berlin');

  if (n >= 30) {
    return commitTimeLocal.toFormat('dd.MM.\HH:mm');
  } else {
    return commitTimeLocal.toFormat('dd.MM.yyyy \n HH:mm');
  }
}

async function getImageData(commitSha) {
  const octokit = new Octokit({
    auth: `token ${token}`,
  });

  try {
    // Get the reference SHA
    const refResponse = await octokit.git.getRef({
      owner,
      repo: repo,
      ref: `graalvm-metrics/${commitSha}`,
    });
    const refSha = refResponse.data.object.sha;

    console.log(refSha)

    // Get the tree SHA
    const treeResponse = await octokit.git.getTree({
      owner,
      repo: repo,
      tree_sha: refSha,
    });
    const blobSha = treeResponse.data.tree[0].sha;

    // Get the blob content
    const blobResponse = await octokit.git.getBlob({
      owner,
      repo: repo,
      file_sha: blobSha,
    });

    const content = Buffer.from(blobResponse.data.content, 'base64').toString('utf-8');
    const data = JSON.parse(content);

    console.log(data.image_details.total_bytes / 1e6)

    return [
      data.image_details.total_bytes / 1e6,
      data.image_details.code_area.bytes / 1e6,
      data.image_details.image_heap.bytes / 1e6,
    ];
  } catch (error) {
    console.error('Error fetching image data:', error.message);
    return [0, 0, 0];
  }
}

// Function to fetch data
async function fetchData() {
  return new Promise(async (resolve, reject) => {

    const response = await octokit.request('https://api.github.com/repos/' + owner + '/' + repo + '/events', {
      headers: {
          "Authorization": "Bearer " + token
      }
    });

    // get push events
    var pushEvents = await getPushEvents(response);

    // Prepare data
    const timestamps = [];
    const shas = [];

    for (const pushEvent of pushEvents) {
      timestamps.push(pushEvent.created_at);
      shas.push(pushEvent.payload.commits[pushEvent.payload.commits.length - 1].sha);
    }

    // Extract data for plotting
    const commitDates = timestamps.map(timestamp => formatDate(timestamp, n));
    const imageDataPromises = shas.map(async sha => await getImageData(sha));
    const imageData = await Promise.all(imageDataPromises);
    const imageSizes = imageData.filter(entry => entry !== 0).map(entry => entry[0]);
    const codeAreaSizes = imageData.filter(entry => entry !== 0).map(entry => entry[1]);
    const imageHeapSizes = imageData.filter(entry => entry !== 0).map(entry => entry[2]);

    const data= {
      commitDates: commitDates,
      imageData: imageData,
      imageSizes: imageSizes,
      codeAreaSizes: codeAreaSizes,
      imageHeapSizes: imageHeapSizes
    }

    resolve(data);
  });
}

async function getPushEvents(response) {
  const eventsArray = response.data;
  var linkHeader = response.headers.link;
  const nextPageMatch = linkHeader.match(/<([^>]+)>;\s*rel="next"/);
  var commitsLeft = n;
  var pushEvents = [];

  for (const event of eventsArray) {
    if (commitsLeft <= 0) {
      break;
    }
    if (event.type === "PushEvent" && event.payload.ref === `refs/heads/${branch}`) {
      pushEvents.push(event);
      commitsLeft -= 1;
    }
  }

  while (linkHeader && linkHeader.includes('rel="next"') && commitsLeft > 0) {
    // Extract the URL for the next page
    const nextPageMatch = linkHeader.match(/<([^>]+)>;\s*rel="next"/);
    const nextPageUrl = nextPageMatch ? nextPageMatch[1] : null;

    // Make the request for the next page
    const response = await fetch(nextPageUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const responseJson = await response.json();

    for (const event of responseJson) {
      if (commitsLeft <= 0) {
        break;
      }
      if (event.type === "PushEvent" && event.payload.ref === `refs/heads/${branch}`) {
        pushEvents.push(event);
        commitsLeft -= 1;
      }
    }

    // Update linkHeader for the next iteration
    linkHeader = response.headers.get("link");
  }
  return pushEvents;
}

function createDatasets(data) {
  const labels = data.commitDates.reverse();

  const datasets = [
    {
      label: 'Image Sizes',
      data: data.imageSizes.reverse(),
      borderColor: 'rgba(75, 192, 192, 1)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      pointRadius: 5,
      pointHoverRadius: 8,
      yAxisID: 'y-axis-1',
    },
    {
      label: 'Code Area Sizes',
      data: data.codeAreaSizes.reverse(),
      borderColor: 'rgba(255, 99, 132, 1)',
      backgroundColor: 'rgba(255, 99, 132, 0.2)',
      pointRadius: 5,
      pointHoverRadius: 8,
      yAxisID: 'y-axis-1',
    },
    {
      label: 'Image Heap Sizes',
      data: data.imageHeapSizes.reverse(),
      borderColor: 'rgba(255, 205, 86, 1)',
      backgroundColor: 'rgba(255, 205, 86, 0.2)',
      pointRadius: 5,
      pointHoverRadius: 8,
      yAxisID: 'y-axis-1',
    },
  ];

  return {
    labels: labels,
    datasets: datasets,
  };
}

async function createChart() {
  try {
    const data = await fetchData();
    const datasets = createDatasets(data);

    console.log(data)

    // Set up canvas
    const canvas = createCanvas(800, 400);
    const ctx = canvas.getContext('2d');

    const config = {
      type: 'line',
      data: datasets,
      options: {
        scales: {
          x: {
            type: 'category',
            title: {
              display: true,
              text: 'Commits',
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.1)', // Brighter color for grid lines
              borderColor: 'rgba(255, 255, 255, 0.2)', // Brighter color for the border of grid lines
            },
          },
          'y-axis-1': {
            type: 'linear',
            position: 'left',
            title: {
              display: true,
              text: 'Size (MB)',
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.1)', // Brighter color for grid lines
              borderColor: 'rgba(255, 255, 255, 0.2)', // Brighter color for the border of grid lines
            },
          },
        },
      },
    };

    Chart.register(...registerables); // Register Chart.js plugins
    const chart = new Chart(ctx, config);

    // Save the canvas as a PNG file
    const out = fs.createWriteStream('output_chart.png');
    const stream = canvas.createPNGStream();
    stream.pipe(out);
    out.on('finish', () => console.log('The PNG file was created.'));
  } catch (error) {
      console.error('Error fetching data:', error);
  }
}

// Call the createChart function
createChart();