import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  ICommandPalette,
  InputDialog,
  Notification,
} from '@jupyterlab/apputils';
import {
  INotebookTracker,
} from '@jupyterlab/notebook';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ITranslator } from '@jupyterlab/translation';

import { requestAPI } from './handler';

const PLUGIN_ID = 'jupyterlab_kishu:plugin';

namespace CommandIDs {
  /**
   * Checkout a commit on the currently viewed file.
   */
  export const checkout = 'kishu:checkout';
}

namespace KishuSetting {
  export let kishu_dir = "";
}

interface CommitSummary {
  commit_id: string;
  parent_id: string;
  message: string;
  timestamp: string;
  code_block?: string;
  runtime_ms?: number;
}

interface LogAllResult {
  commit_graph: CommitSummary[];
}

interface CheckoutResult {
  status: string;
  message: string;
}

function notifyError(message: string) {
  Notification.error(message, { autoClose: 3000 });
}

function commitSummaryToString(commit: CommitSummary): string {
  return `[${commit.commit_id}] ${commit.message}`;
}

function extractHashFromString(inputString: string): string | undefined {
  const regex = /\[([a-fA-F0-9-]+)\]\s/;
  const match = inputString.match(regex);
  if (match && match[1]) {
    return match[1];
  }
  return undefined;
}

function loadSetting(setting: ISettingRegistry.ISettings): void {
  // Read the settings and convert to the correct type
  KishuSetting.kishu_dir = setting.get('kishu_dir').composite as string;
  console.log(`Settings: kishu_dir= ${KishuSetting.kishu_dir}`);
}

function installCommands(
  app: JupyterFrontEnd,
  palette: ICommandPalette,
  translator: ITranslator,
  tracker: INotebookTracker,
) {
  const { commands } = app;
  const trans = translator.load('jupyterlab');

  /**
   * Checkout
   */

  commands.addCommand(CommandIDs.checkout, {
    label: trans.__('Kishu: Checkout...'),
    execute: async (_args) => {
      // Detect currently viewed notebook.
      const widget = tracker.currentWidget;
      if (!widget) {
        notifyError(trans.__(`No currently viewed notebook detected to checkout (missing widget).`));
        return;
      }
      const notebook_path = widget.context.localPath;
      if (!notebook_path) {
        notifyError(trans.__(`No currently viewed notebook detected to checkout.`));
        return;
      }

      // List all commits.
      const log_all_result = await requestAPI<LogAllResult>('log_all', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path}),
      });

      // Ask for the target commit ID.
      let maybe_commit_id = undefined;
      if (!log_all_result || log_all_result.commit_graph.length == 0) {
        // Failed to list, asking in text dialog directly.
        maybe_commit_id = (
          await InputDialog.getText({
            placeholder: '<commit_id>',
            title: trans.__('Checkout to...'),
            okLabel: trans.__('Checkout')
          })
        ).value ?? undefined;
      } else {
        // Show the list and ask to pick one item
        const selected_commit_str = (
          await InputDialog.getItem({
            items: log_all_result.commit_graph.map(commitSummaryToString),
            current: log_all_result.commit_graph.length - 1,
            editable: false,
            title: trans.__('Checkout to...'),
            okLabel: trans.__('Checkout')
          })
        ).value ?? undefined;
        if (selected_commit_str !== undefined) {
          maybe_commit_id = extractHashFromString(selected_commit_str);
        }
      }
      if (!maybe_commit_id) {
        notifyError(trans.__(`Kishu checkout requires commit ID.`));
        return;
      }
      const commit_id: string = maybe_commit_id;

      // Make checkout request
      const checkout_promise = requestAPI<CheckoutResult>('checkout', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path, commit_id: commit_id}),
      });

      // Reports.
      const notify_manager = Notification.manager;
      const notify_id = notify_manager.notify(
        trans.__(`Checking out ${commit_id}...`),
        'in-progress',
        { autoClose: false },
      );
      checkout_promise.then((checkout_result,) => {
        if (checkout_result.status != "ok") {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu checkout failed: "${checkout_result.message}"`),
            type: 'error',
            autoClose: 3000,
          });
        } else {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu checkout to ${commit_id} succeeded.\nPlease refresh this page.`),
            type: 'success',
            autoClose: 3000,
          });
        }
      });
    }
  });
  palette.addItem({
    command: CommandIDs.checkout,
    category: 'Kishu',
  });
}

/**
 * Initialization data for the jupyterlab_kishu extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description: 'Jupyter extension to interact with Kishu',
  autoStart: true,
  requires: [ICommandPalette, ITranslator, ISettingRegistry, INotebookTracker],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    translator: ITranslator,
    settings: ISettingRegistry,
    tracker: INotebookTracker,
  ) => {
    Promise.all([app.restored, settings.load(PLUGIN_ID)])
      .then(([, setting]) => {
        // Setting registry.
        loadSetting(setting);
        setting.changed.connect(loadSetting);

        // Install commands.
        installCommands(app, palette, translator, tracker);
      })
      .catch(reason => {
        console.error(
          `Something went wrong when reading the settings.\n${reason}`
        );
      });
  }
};

export default plugin;
